from pathlib import Path

import pandas as pd
import torch

from fastapi_app.services.embedding_e5 import encode_texts

# --------------------
# 경로 & 설정
# --------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "rsos_dream_data.tsv"
OUT_DIR = BASE_DIR / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EMB_FILE = OUT_DIR / "e5_embeddings_labels.pt"
EMB_PARTIAL_FILE = OUT_DIR / "e5_embeddings_labels_partial.pt"

BATCH_SIZE = 256      # GPU 충분하니까 크게 가져가도 됨
SAVE_EVERY = 1000     # N개 처리할 때마다 partial 저장

TEXT_COL = "text_dream"
VALENCE_COL = "NegativeEmotions"

# facet index 원본 컬럼 (연속값)
RAW_FACET_COLS = ["A/CIndex", "F/CIndex", "S/CIndex"]
# 이걸 기준으로 만든 이진 facet 라벨 컬럼
FACET_BIN_COLS = ["facet_aggr", "facet_friend", "facet_sex"]


def main():
    # 1) TSV 로드
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, sep="\t")
    print("컬럼 확인:", df.columns.tolist())

    print(f"총 {len(df)}개 샘플을 사용합니다.")

    # 2) Valence 라벨 생성 (NegativeEmotions > 0 → 1, else 0)
    if VALENCE_COL not in df.columns:
        raise ValueError(f"'{VALENCE_COL}' 컬럼이 데이터에 없습니다.")

    df["valence_label"] = (df[VALENCE_COL] > 0).astype("float32")

    # 3) 텍스트 및 facet index 컬럼 확인
    if TEXT_COL not in df.columns:
        raise ValueError(f"텍스트 컬럼 '{TEXT_COL}' 이(가) 데이터에 없습니다.")

    for col in RAW_FACET_COLS:
        if col not in df.columns:
            raise ValueError(f"raw facet 컬럼 '{col}' 이(가) 데이터에 없습니다.")

    # facet index 를 float 으로 변환 (문자/NaN 처리)
    for col in RAW_FACET_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df[RAW_FACET_COLS] = df[RAW_FACET_COLS].fillna(0.0)

    # 이진 facet 라벨: index > 0 이면 1, 아니면 0
    df["facet_aggr"] = (df["A/CIndex"] > 0).astype("float32")
    df["facet_friend"] = (df["F/CIndex"] > 0).astype("float32")
    df["facet_sex"] = (df["S/CIndex"] > 0).astype("float32")

    # 텍스트 리스트
    texts = df[TEXT_COL].astype(str).tolist()
    num_texts = len(texts)

    print(f"총 문장 수: {num_texts}, 배치 크기: {BATCH_SIZE}")

    # 4) 임베딩 추출 (배치 단위)
    all_embeddings = []

    for i in range(0, num_texts, BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        emb = encode_texts(batch_texts)  # (B, H) CPU 텐서
        all_embeddings.append(emb)

        done = i + len(batch_texts)
        print(f"{done} / {num_texts} 개 처리 완료")

        # N개마다 partial 저장
        if (done % SAVE_EVERY == 0) or (done == num_texts):
            embeddings = torch.cat(all_embeddings, dim=0)  # (done, H)
            print("현재 임베딩 텐서 크기:", embeddings.shape)

            valence = torch.from_numpy(
                df["valence_label"].to_numpy(dtype="float32")[:done]
            )  # (done,)
            facets = torch.from_numpy(
                df[FACET_BIN_COLS].to_numpy(dtype="float32")[:done]
            )  # (done, 3)

            partial_payload = {
                "embeddings": embeddings,
                "valence": valence,
                "facets": facets,
                "index": df["dream_id"].to_numpy()[:done]
                if "dream_id" in df.columns
                else None,
                "columns": {
                    "text": TEXT_COL,
                    "valence": VALENCE_COL,
                    "facets": FACET_BIN_COLS,
                },
            }

            torch.save(partial_payload, EMB_PARTIAL_FILE)
            print(f"⏺ {done}개까지 중간 저장 완료: {EMB_PARTIAL_FILE}")

    # 5) 최종 전체 저장
    embeddings = torch.cat(all_embeddings, dim=0)  # (N, H)
    valence = torch.from_numpy(
        df["valence_label"].to_numpy(dtype="float32")
    )  # (N,)
    facets = torch.from_numpy(
        df[FACET_BIN_COLS].to_numpy(dtype="float32")
    )  # (N, 3)

    payload = {
        "embeddings": embeddings,
        "valence": valence,
        "facets": facets,
        "index": df["dream_id"].to_numpy()
        if "dream_id" in df.columns
        else None,
        "columns": {
            "text": TEXT_COL,
            "valence": VALENCE_COL,
            "facets": FACET_BIN_COLS,
        },
    }

    torch.save(payload, EMB_FILE)
    print("최종 임베딩 텐서 크기:", embeddings.shape)
    print("최종 저장 완료:", EMB_FILE)


if __name__ == "__main__":
    main()
