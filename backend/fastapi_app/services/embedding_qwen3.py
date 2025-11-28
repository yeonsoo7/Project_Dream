# embedding_qwen3.py
from functools import lru_cache
from typing import List
import torch
from transformers import AutoTokenizer, AutoModel

MODEL_NAME = "intfloat/multilingual-e5-base"

@lru_cache(maxsize=1)
def get_model_and_tokenizer():
    """
    모델과 토크나이저를 서버 시작 시 1번만 로드하고 캐싱한다.
    """
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.eval()  # 추론 모드
    return tokenizer, model


def mean_pooling(model_output, attention_mask):
    """
    Mean Pooling 방식으로 문장의 임베딩을 계산
    """
    token_embeddings = model_output.last_hidden_state  # (B, L, H)
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size())
    sum_embeddings = (token_embeddings * input_mask_expanded).sum(1)
    sum_mask = input_mask_expanded.sum(1)
    return sum_embeddings / sum_mask  # (B, H)


def encode_texts(texts: List[str]) -> torch.Tensor:
    """
    입력: 리스트[str]
    출력: torch.Tensor (batch_size, hidden_dim)
    """
    tokenizer, model = get_model_and_tokenizer()

    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model(**encoded)
        embeddings = mean_pooling(outputs, encoded["attention_mask"])

    return embeddings  # (B, H)
