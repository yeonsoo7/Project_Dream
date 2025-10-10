import argparse, os, sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

print("[VALENCE] import transformers/datasets ...")
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1": f1_score(labels, preds, average="macro"),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="ml/data/valence.csv")
    ap.add_argument("--model-name", default="distilbert-base-uncased")
    ap.add_argument("--outdir", default="ml/outputs/valence_model")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=16)
    args = ap.parse_args()

    print(f"[VALENCE] args={args}")
    if not os.path.exists(args.data):
        print(f"[VALENCE][ERR] data not found: {args.data}", file=sys.stderr); sys.exit(2)

    df = pd.read_csv(args.data).dropna().reset_index(drop=True)
    if "text" not in df.columns or "label" not in df.columns:
        print(f"[VALENCE][ERR] CSV must have columns: text,label. got={list(df.columns)}", file=sys.stderr); sys.exit(2)
    print(f"[VALENCE] data shape={df.shape}")

    train_df, eval_df = train_test_split(df, test_size=0.1, stratify=df["label"], random_state=42)

    tok = AutoTokenizer.from_pretrained(args.model_name)
    def tokenize(ex): return tok(ex["text"], truncation=True, max_length=512)

    train_ds = Dataset.from_pandas(train_df[["text","label"]]).map(tokenize, batched=True)
    eval_ds  = Dataset.from_pandas(eval_df[["text","label"]]).map(tokenize, batched=True)
    print(f"[VALENCE] ds sizes: train={len(train_ds)} eval={len(eval_ds)}")

    model = AutoModelForSequenceClassification.from_pretrained(args.model_name, num_labels=2)

    # ★ 호환 모드: 최신 인자(evaluation_strategy 등) 제거
    training_args = TrainingArguments(
        output_dir=args.outdir,
        learning_rate=3e-5,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        logging_steps=25,
        report_to=[] if "report_to" in TrainingArguments.__init__.__code__.co_varnames else None,
    )

    print("[VALENCE] start training ...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,          # 수동 평가에 씀
        tokenizer=tok,
        compute_metrics=compute_metrics,
    )
    trainer.train()

    print("[VALENCE] manual evaluate ...")
    metrics = trainer.evaluate()
    print("[VALENCE] eval metrics:", metrics)

    print("[VALENCE] saving ...")
    trainer.save_model(args.outdir); tok.save_pretrained(args.outdir)
    print(f"[VALENCE] saved to {args.outdir}")

if __name__ == "__main__":
    main()
