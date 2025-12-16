import os
from functools import lru_cache
from typing import List

import torch
from transformers import AutoTokenizer, AutoModel

MODEL_NAME = "intfloat/multilingual-e5-base"

# 토크나이저 병렬 처리 활성화 (속도 ↑)
os.environ["TOKENIZERS_PARALLELISM"] = "true"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=1)
def get_model_and_tokenizer():
    """
    E5 임베딩 모델과 토크나이저를 한 번만 로딩해서 캐시.
    - FP16 + device_map="auto" 로 GPU 활용
    - Fast tokenizer 사용
    """
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
    )

    model = AutoModel.from_pretrained(
        MODEL_NAME,
        dtype=torch.float16,   # FP16 (PyTorch 2.6에서는 dtype 사용)
        device_map="auto",
    )

    model.eval()
    return tokenizer, model


def mean_pooling(model_output, attention_mask):
    """
    Mean Pooling: 토큰 히든스테이트를 마스크 기준으로 평균내서 문장 벡터로 변환
    """
    token_embeddings = model_output.last_hidden_state  # (B, L, H)
    mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size())
    sum_embeddings = (token_embeddings * mask_expanded).sum(1)
    sum_mask = mask_expanded.sum(1)
    return sum_embeddings / sum_mask  # (B, H)


def encode_texts(texts: List[str]) -> torch.Tensor:
    """
    입력: 문자열 리스트 (batch)
    출력: torch.Tensor (batch_size, hidden_dim=768)
    """
    tokenizer, model = get_model_and_tokenizer()

    # 바로 GPU로 올리기
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt",
    ).to(DEVICE)

    with torch.no_grad():
        outputs = model(**encoded)
        embeddings = mean_pooling(outputs, encoded["attention_mask"])

    # 나중에 CPU에서 concat / 학습할 수 있도록 CPU로 돌려보냄
    return embeddings.cpu()  # (B, H)
