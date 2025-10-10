import argparse
import pandas as pd
from pathlib import Path

FACETS = ["aggression","conflict","friendliness","sexuality","success","misfortune"]

def safe_to_float(x):
    """숫자로 바꿀 수 있으면 float으로, 아니면 0으로."""
    try:
        return float(x)
    except Exception:
        return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Raw CSV path from Dryad (merged or main)")
    ap.add_argument("--text-col", default="text_dream", help="Column name for dream text")
    # valence: either provide a single col with 'pos/neg' or prob columns
    ap.add_argument("--valence-col", default=None, help="Column with 'pos' or 'neg' strings (optional)")
    ap.add_argument("--neg-col", default="neg", help="Column with negative score/flag (optional)")
    ap.add_argument("--pos-col", default="pos", help="Column with positive score/flag (optional)")
    # facet columns (binary 0/1 or boolean or probs)
    ap.add_argument("--aggr-col", default="aggression")
    ap.add_argument("--conf-col", default="conflict")
    ap.add_argument("--frnd-col", default="friendliness")
    ap.add_argument("--sex-col",  default="sexuality")
    ap.add_argument("--succ-col", default="success")
    ap.add_argument("--misf-col", default="misfortune")
    ap.add_argument("--outdir", default="ml/data", help="Output dir")
    ap.add_argument("--sep", default="\t", help="CSV separator, default ','")
    ap.add_argument("--derive-valence", action="store_true",
                    help="Derive valence label as 1 if friendliness >= aggression, else 0.")

    args = ap.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.input, sep=args.sep, engine="python")

    if args.text_col not in df.columns:
        raise ValueError(f"Text column '{args.text_col}' not found. Available: {list(df.columns)[:20]}")

    # ---------- Valence ----------
    if args.valence_col and args.valence_col in df.columns:
        val_map = {"positive":1, "pos":1, "neg":0, "negative":0, 1:1, 0:0}
        valence = df[[args.text_col, args.valence_col]].dropna()
        valence["label"] = valence[args.valence_col].map(lambda x: val_map.get(str(x).strip().lower(), None))
        valence = valence[valence["label"].notnull()]
        valence = valence.rename(columns={args.text_col: "text"})[["text","label"]]
    elif (args.neg_col in df.columns) and (args.pos_col in df.columns):
        # derive from two numeric/flag columns (neg vs pos)
        for c in [args.neg_col, args.pos_col]:
            if c not in df.columns:
                raise ValueError(f"Valence columns '{args.neg_col}', '{args.pos_col}' not found.")
        valence = df[[args.text_col, args.neg_col, args.pos_col]].dropna()
        valence = valence.rename(columns={args.text_col:"text"})
        # label = 1 if pos >= neg else 0
        valence["label"] = (valence[args.pos_col].astype(float) >= valence[args.neg_col].astype(float)).astype(int)
        valence = valence[["text","label"]]
    elif args.derive_valence:
        # derive from friendliness vs aggression
        if args.aggr_col not in df.columns or args.frnd_col not in df.columns:
            raise ValueError("derive-valence requested but aggr/frnd columns not found")
        valence = df[[args.text_col, args.aggr_col, args.frnd_col]].dropna()
        valence = valence.rename(columns={args.text_col:"text"})
        # 안전하게 숫자 변환
        valence[args.aggr_col] = valence[args.aggr_col].apply(safe_to_float)
        valence[args.frnd_col] = valence[args.frnd_col].apply(safe_to_float)
        valence["label"] = (valence[args.frnd_col].astype(float) >= valence[args.aggr_col].astype(float)).astype(int)
        valence = valence[["text","label"]]
    else:
        raise ValueError(
            "No valence source found. Provide --valence-col OR --neg-col/--pos-col OR --derive-valence."
        )

    valence.to_csv(outdir / "valence.csv", index=False)

    # ---------- Facets ----------
    col_map = {
        "aggression": args.aggr_col,
        "conflict": args.conf_col,
        "friendliness": args.frnd_col,
        "sexuality": args.sex_col,
        "success": args.succ_col,
        "misfortune": args.misf_col,
    }
    missing = [c for c in col_map.values() if c not in df.columns]
    if missing:
        print(f"[WARN] facet columns missing {missing} → facets.csv will include only existing ones.")
    fcols = {k:v for k,v in col_map.items() if v in df.columns}

    facets = df[[args.text_col] + list(fcols.values())].dropna().rename(columns={args.text_col:"text"})
    # # binarize (>=0.5 -> 1) if numeric, otherwise cast bool->int
    # for k, src in fcols.items():
    #     try:
    #         facets[k] = (facets[src].astype(float) >= 0.5).astype(int)
    #     except Exception:
    #         facets[k] = facets[src].astype(int)
    # facets = facets[["text"] + list(fcols.keys())]

    # 문자열 코드 → 0/1 로 단순화 (값이 비어있지 않으면 1)
    for k, src in fcols.items():
        facets[k] = facets[src].apply(lambda x: 1 if str(x).strip() != "" else 0)

    # ensure all 6 exist (fill 0 if missing)
    for f in FACETS:
        if f not in facets.columns:
            facets[f] = 0
    facets = facets[["text"] + FACETS]
    facets.to_csv(outdir / "facets.csv", index=False)

    print(f"[OK] Wrote: {outdir/'valence.csv'} , {outdir/'facets.csv'}")

if __name__ == "__main__":
    main()
