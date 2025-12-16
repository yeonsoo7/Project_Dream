# fastapi_app/services/dream_analyzer.py

from pathlib import Path
from functools import lru_cache
from typing import Dict, Any

import torch
import torch.nn as nn

from fastapi_app.services.embedding_e5 import encode_texts


# =========================
# 경로 & 공통 설정
# =========================

# 이 파일 위치: fastapi_app/services/
BASE_DIR = Path(__file__).resolve().parent  # services/
APP_DIR = BASE_DIR.parent                   # fastapi_app/
ML_DIR = APP_DIR / "ml_artifacts" / "e5"

VALENCE_MODEL_PATH = ML_DIR / "valence_e5_classifier.pt"
FACETS_MODEL_PATH = ML_DIR / "facets_e5_classifier.pt"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# =========================
# MLP 구조 (훈련 때와 동일)
# =========================

class MLP(nn.Module):
    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 256),
            nn.ReLU(),
            nn.Linear(256, out_dim),
        )

    def forward(self, x):
        return self.net(x)


# =========================
# 분류기 로딩 (1번만)
# =========================

@lru_cache(maxsize=1)
def _load_e5_classifiers():
    """
    E5 임베딩 위에서 동작하는
    - valence 이진 분류기 (1차원 출력)
    - facets 멀티라벨 분류기 (3차원 출력: aggression / friendliness / sexuality)
    를 로딩해서 반환.
    """
    val_model = MLP(768, 1)
    fac_model = MLP(768, 3)

    # torch.load 기본값이 weights_only=True라서 False 명시
    state_val = torch.load(
        VALENCE_MODEL_PATH,
        map_location="cpu",
        weights_only=False,
    )
    state_fac = torch.load(
        FACETS_MODEL_PATH,
        map_location="cpu",
        weights_only=False,
    )

    val_model.load_state_dict(state_val)
    fac_model.load_state_dict(state_fac)

    val_model.eval()
    fac_model.eval()

    # 원하면 여기서 .to(DEVICE) 해서 GPU로 옮겨도 됨
    return val_model, fac_model


# =========================
# 실제 분석 로직 (E5 + 분류기)
# =========================

@torch.no_grad()
def analyze_dream_with_e5(text: str) -> Dict[str, Any]:
    """
    입력: 한국어 꿈 텍스트 1개
    출력: valence + facets 예측 결과(dic 형식)

    - valence: 0=non_negative(비부정), 1=negative(부정)
    - facets:
        aggression: 0/1
        friendliness: 0/1
        sexuality: 0/1
    """
    # 1) E5 임베딩 추출 (1, 768)
    emb = encode_texts([text])   # (1, 768), CPU 텐서
    emb = emb.float()            # 분류기는 float32로 학습됨

    # 2) 분류기 로딩
    val_model, fac_model = _load_e5_classifiers()

    # 3) Valence 예측
    val_logit = val_model(emb).squeeze(1)          # (1,)
    val_prob_neg = torch.sigmoid(val_logit).item() # 부정일 확률 P(negative)
    val_label = 1 if val_prob_neg > 0.5 else 0     # 1: negative, 0: non_negative

    # 4) Facets 예측 (aggression / friendliness / sexuality)
    fac_logits = fac_model(emb)                    # (1, 3)
    fac_probs = torch.sigmoid(fac_logits).squeeze(0)  # (3,)
    p_aggr, p_friend, p_sex = [float(x) for x in fac_probs.tolist()]

    l_aggr = 1 if p_aggr > 0.5 else 0
    l_friend = 1 if p_friend > 0.5 else 0
    l_sex = 1 if p_sex > 0.5 else 0

    # 5) 결과 포맷 (valence / facets 키 구조 유지)
    val_prob_pos = float(1.0 - val_prob_neg)  # 비부정(positive)에 해당
    result: Dict[str, Any] = {
        "valence": {
            # 0: non_negative, 1: negative
            "label": int(val_label),
            "label_str": "negative" if val_label == 1 else "non_negative",

            # 새 형식
            "prob_negative": float(val_prob_neg),
            "prob_non_negative": val_prob_pos,

            # 옛날 DreamAnalysis.from_result가 기대하는 키 (호환용)
            "negative": float(val_prob_neg),
            "positive": val_prob_pos,
        },
        "facets": {
            # labels: 0/1
            "labels": {
                "aggression": int(l_aggr),
                "friendliness": int(l_friend),
                "sexuality": int(l_sex),
            },
            # 확률 값
            "probs": {
                "aggression": p_aggr,
                "friendliness": p_friend,
                "sexuality": p_sex,
            },
        },
    }

    return result


# =========================
# 기존 인터페이스 유지용 래퍼
# =========================

class DreamAnalyzer:
    """
    기존 코드에서 쓰던 싱글톤 접근:
        DreamAnalyzer.get().analyze(text)

    을 그대로 유지하면서 내부 구현만
    E5 임베딩 + 새 분류기로 교체한 버전.
    """

    _instance: "DreamAnalyzer | None" = None

    @classmethod
    def get(cls) -> "DreamAnalyzer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # 미리 로딩해 두면 매 호출마다 load 안 해도 됨
        self.val_model, self.fac_model = _load_e5_classifiers()

    @torch.no_grad()
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        API에서 사용하는 메인 진입점.
        내부적으로 analyze_dream_with_e5를 호출.
        """
        # 여기서는 위의 공통 함수 재사용
        return analyze_dream_with_e5(text)
