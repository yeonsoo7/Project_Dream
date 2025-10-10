# backend/fastapi_app/services/dream_analyzer.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from fastapi_app.services.evidence_rules import extract_evidence_candidates

# 모델 가중치가 놓일 위치: backend/fastapi_app/ml_artifacts/{valence,facets}
ART_DIR = Path(__file__).resolve().parents[1] / "ml_artifacts"


class DreamAnalyzer:
    """
    싱글턴 형태로 로딩 비용을 한 번만 지는 추론 클래스.
    - 헤드1: valence(긍/부정) 이진 분류
    - 헤드2: facets(공격성/갈등/우호성/성공/불운/성적요소) 멀티라벨
    - evidence: 규칙 기반 근거문장 추출(초기 버전)
    """
    _instance: "DreamAnalyzer | None" = None

    @staticmethod
    def get() -> "DreamAnalyzer":
        if DreamAnalyzer._instance is None:
            DreamAnalyzer._instance = DreamAnalyzer()
        return DreamAnalyzer._instance

    def __init__(self) -> None:
        # ---- Valence (binary: [neg, pos] 순서로 학습했다고 가정) ----
        valence_dir = ART_DIR / "valence"
        if not valence_dir.exists():
            raise RuntimeError(f"Valence model not found: {valence_dir}")
        self.tok_val = AutoTokenizer.from_pretrained(str(valence_dir))
        self.model_val = AutoModelForSequenceClassification.from_pretrained(str(valence_dir)).eval()

        # ---- Facets (multi-label) ----
        facets_dir = ART_DIR / "facets"
        if not facets_dir.exists():
            raise RuntimeError(f"Facets model not found: {facets_dir}")
        self.facets = ["aggression", "conflict", "friendliness", "sexuality", "success", "misfortune"]
        self.tok_fac = AutoTokenizer.from_pretrained(str(facets_dir))
        self.model_fac = AutoModelForSequenceClassification.from_pretrained(str(facets_dir)).eval()

    @torch.inference_mode()
    def analyze(self, text: str) -> Dict:
        # 1) Valence
        inp_v = self.tok_val(text, return_tensors="pt", truncation=True, max_length=512)
        logits_v = self.model_val(**inp_v).logits  # shape: [1, 2]
        probs_v = torch.softmax(logits_v, dim=-1)[0].tolist()  # [neg, pos]
        valence = {"positive": float(probs_v[1]), "negative": float(probs_v[0])}

        # 2) Facets (sigmoid multi-label)
        inp_f = self.tok_fac(text, return_tensors="pt", truncation=True, max_length=512)
        logits_f = self.model_fac(**inp_f).logits[0]  # shape: [num_labels]
        probs_f = torch.sigmoid(logits_f).tolist()
        facets = {k: float(v) for k, v in zip(self.facets, probs_f)}

        # 3) Evidence (간단 규칙 기반 하이라이트)
        evidence = extract_evidence_candidates(text, facets)

        # 4) 간단 설명 문구(NLG 템플릿)
        notes: List[str] = []
        if facets.get("aggression", 0.0) > 0.6:
            notes.append("공격성 신호가 높습니다(무기/추격/폭력 표현).")
        if facets.get("conflict", 0.0) > 0.6:
            notes.append("갈등/대립 묘사가 중심입니다.")
        if valence["negative"] > 0.6 and facets.get("success", 0.0) < 0.4:
            notes.append("해결/극복 신호가 약해 전반적으로 부정으로 평가됩니다.")

        return {
            "valence": valence,
            "facets": facets,
            "evidence": evidence,
            "nlg_notes": notes[:3],
        }
