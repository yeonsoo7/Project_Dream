from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Any
import json
import torch
import re, math

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

ALL_FACETS = ["aggression","conflict","friendliness","sexuality","success","misfortune"]

NEG_PATTERNS = [
    r"괴물", r"무섭\w*", r"두려\w*", r"공포", r"쫓\w*", r"도망\w*", r"숨\w*", r"위협",
    r"피하\w*", r"불안\w*", r"악몽", r"울\w*", r"불행", r"공격\w*", r"싸움", r"분노"
]
POS_PATTERNS = [
    r"행복\w*", r"즐겁\w*", r"기쁘\w*", r"재밌\w*", r"안전\w*", r"안도\w*", r"평온\w*",
    r"성공\w*", r"포옹"
]
STRONG_THREAT = [r"괴물", r"쫓\w*", r"도망\w*", r"숨\w*", r"위협", r"공포"]

def _count_hits(patterns: List[str], text: str) -> int:
    return sum(1 for p in patterns if re.search(p, text))

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def _logit(p: float, eps: float = 1e-6) -> float:
    p = min(max(p, eps), 1 - eps)
    return math.log(p / (1 - p))

def _tweak_ko_valence_strong(text: str, valence: Dict[str, float]) -> Dict[str, float]:
    pos0 = float(valence.get("positive", 0.0))
    neg0 = 1.0 - pos0

    neg_hits = _count_hits(NEG_PATTERNS, text)
    pos_hits = _count_hits(POS_PATTERNS, text)
    strong_threat_hits = _count_hits(STRONG_THREAT, text)

    logit_pos = _logit(pos0)
    # ---- Bias 계산 ----
    if strong_threat_hits >= 1:
        # 위협 단서가 있는 경우만 강한 부정 보정
        bias = (-0.85 * min(1, strong_threat_hits)) + (-0.20 * max(0, neg_hits - strong_threat_hits)) + (0.12 * pos_hits)
    else:
        # 위협 단서가 전혀 없을 경우, 약간 긍정 쪽으로 보정
        bias = (0.15 * pos_hits) - (0.05 * neg_hits)

    pos1 = _sigmoid(logit_pos + bias)

    # 강제 플로어/실링 조정
    # 위협 단서가 있고, 긍정이 과도하게 높으면서 긍정 패턴은 없을 때
    # → 강제 하한선을 0.35로 깎아서 “무서운 상황인데 너무 긍정적”인 상황 방지
    if strong_threat_hits >= 1 and pos1 > 0.40 and pos_hits == 0:
        pos1 = 0.35
    if neg_hits >= 2 and pos_hits == 0 and pos1 > 0.45:
        pos1 = 0.40

    pos1 = float(max(0.0, min(1.0, pos1)))
    return {"positive": pos1, "negative": 1.0 - pos1}


def _tweak_ko_facets_strong(text: str, facets: Dict[str, float]) -> Dict[str, float]:
    out = dict(facets)
    if _count_hits(STRONG_THREAT, text) >= 1:
        out["conflict"]   = max(out.get("conflict", 0.0),   0.70)
        out["aggression"] = max(out.get("aggression", 0.0), 0.62)
        out["misfortune"] = max(out.get("misfortune", 0.0), 0.58)
    if _count_hits([r"함께", r"친구", r"도와\w*", r"안전"], text) >= 1:
        out["friendliness"] = max(out.get("friendliness", 0.0), 0.50)
    return out

class DreamAnalyzer:
    _instance: "DreamAnalyzer|None" = None

    def __init__(self):
        # 서비스 파일 기준으로 아티팩트 절대경로 계산
        base = Path(__file__).resolve().parent.parent / "ml_artifacts"
        self.valence_dir = (base / "valence").resolve()
        self.facets_dir  = (base / "facets").resolve()

        if not self.valence_dir.exists():
            raise RuntimeError(f"Valence artifacts not found: {self.valence_dir}")
        if not self.facets_dir.exists():
            raise RuntimeError(f"Facets artifacts not found: {self.facets_dir}")

        # 디바이스 (CUDA 없으면 CPU)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # --- valence (이진) ---
        self.val_tok = AutoTokenizer.from_pretrained(str(self.valence_dir))
        self.val_model = AutoModelForSequenceClassification.from_pretrained(str(self.valence_dir))
        self.val_model.to(self.device).eval()

        # --- facets (멀티라벨) ---
        self.fac_tok = AutoTokenizer.from_pretrained(str(self.facets_dir))
        self.fac_model = AutoModelForSequenceClassification.from_pretrained(str(self.facets_dir))
        self.fac_model.to(self.device).eval()

        # facets 라벨 목록 (활성 라벨만 있을 수 있음)
        labels_path = self.facets_dir / "labels.json"
        if labels_path.exists():
            with labels_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self.active_facets: List[str] = data.get("labels", ALL_FACETS)
        else:
            # labels.json이 없으면 6개 전부라고 가정
            self.active_facets = ALL_FACETS

    @classmethod
    def get(cls) -> "DreamAnalyzer":
        if cls._instance is None:
            cls._instance = DreamAnalyzer()
        return cls._instance

    @torch.inference_mode()
    def analyze(self, text: str) -> Dict[str, Any]:
        # ----- valence -----
        v_inputs = self.val_tok(
            text, return_tensors="pt", truncation=True, padding=True, max_length=256
        ).to(self.device)
        v_logits = self.val_model(**v_inputs).logits  # shape [1,2]
        v_probs = torch.softmax(v_logits, dim=-1).squeeze(0).tolist()
        # HF 이진 클래스는 [NEG, POS] 순서인 경우가 많음 — 안전하게 정렬
        if len(v_probs) == 2:
            negative, positive = float(v_probs[0]), float(v_probs[1])
        else:
            # 비정상 구조 대비
            positive, negative = float(v_probs[-1]), 1.0 - float(v_probs[-1])

        valence = {"positive": positive, "negative": negative}

        # ----- facets (multi-label) -----
        f_inputs = self.fac_tok(
            text, return_tensors="pt", truncation=True, padding=True, max_length=256
        ).to(self.device)
        f_logits = self.fac_model(**f_inputs).logits  # shape [1, num_active]
        f_probs = torch.sigmoid(f_logits).squeeze(0).tolist()

        # active 라벨만 확률이 있으므로, 전체 6개 키로 확장
        facets = {k: 0.0 for k in ALL_FACETS}
        for k, p in zip(self.active_facets, f_probs):
            facets[k] = float(p)

        # ----- 한국어 보정 레이어 -----
        valence = _tweak_ko_valence_strong(text, valence)
        facets  = _tweak_ko_facets_strong(text, facets)

        if max(facets.get("conflict", 0.0), facets.get("aggression", 0.0), facets.get("misfortune", 0.0)) >= 0.65:
            if valence["positive"] > 0.45 and _count_hits(POS_PATTERNS, text) == 0:
                valence["positive"] = 0.35
                valence["negative"] = 0.65

        # ----- 간단한 설명 문장 생성 -----
        notes: List[str] = []
        if facets.get("friendliness", 0) > 0.6 and valence["positive"] > 0.6:
            notes.append("우호성이 높고 전반적으로 긍정적인 정서입니다.")
        if facets.get("aggression", 0) > 0.6 or facets.get("conflict", 0) > 0.6:
            notes.append("공격성/갈등 관련 단서가 비교적 높게 탐지됐습니다.")
        if facets.get("sexuality", 0) > 0.6:
            notes.append("성적 맥락의 단서가 관찰됩니다.")
        if not notes:
            notes.append("뚜렷한 특정 요소는 낮고, 중립에 가깝습니다.")

        evidence = {
            "neg_patterns": [
                {"pattern": p, "matched": bool(re.search(p, text))}
                for p in NEG_PATTERNS
            ],
            "pos_patterns": [
                {"pattern": p, "matched": bool(re.search(p, text))}
                for p in POS_PATTERNS
            ],
        }

        return {
            "valence": valence,
            "facets": facets,
            "nlg_notes": notes,
            "evidence": evidence,
        }
