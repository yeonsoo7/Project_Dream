from pathlib import Path

import pandas as pd
import torch

from fastapi_app.services.embedding_qwen3 import encode_texts

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "rsos_dream_data.tsv"   # ← 실제 파일명
OUT_DIR = BASE_DIR / "data" / "processed"

BATCH_SIZE = 32


def main():
    # 1) TSV 로드
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, sep="\t")

    print("컬럼 확인:", df.columns.tolist()[:10])
    df = df.head(1000).copy()
    
    # 2) valence_label 생성: NegativeEmotions > 0 인 경우 1, 아니면 0
    if "NegativeEmotions" not in df.columns:
        raise ValueError("컬럼 'NegativeEmotions' 를 찾을 수 없습니다.")

    df["valence_label"] = (df["NegativeEmotions"] > 0).astype(int)

    # 3) 텍스트 / facet 컬럼 이름 정의
    text_col = "text_dream"
    if text_col not in df.columns:
        raise ValueError(f"텍스트 컬럼 '{text_col}' 를 찾을 수 없습니다.")

    facet_cols = ["aggression_code", "friendliness_code", "sexuality_code"]
    for col in facet_cols:
        if col not in df.columns:
            raise ValueError(f"facet 컬럼이 없습니다: {col}")

    texts = df[text_col].astype(str).tolist()

    # 4) Qwen 임베딩 뽑기
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        emb = encode_texts(batch_texts)  # (B, H) torch.Tensor
        all_embeddings.append(emb)

    embeddings = torch.cat(all_embeddings, dim=0)  # (N, H)

    # 5) 라벨 텐서로 변환
    valence = torch.tensor(df["valence_label"].values, dtype=torch.float32)
    facets = torch.tensor(df[facet_cols].values, dtype=torch.float32)

    # 6) 저장
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / "qwen3_embeddings.pt"

    torch.save(
        {
            "embeddings": embeddings,   # (N, H)
            "valence": valence,         # (N,)
            "facets": facets,           # (N, num_facets)
            "facet_cols": facet_cols,   # 나중에 어떤 facet인지 기억용
        },
        out_file,
    )

    print(f"임베딩 및 라벨 저장 완료: {out_file}")


if __name__ == "__main__":
    main()
