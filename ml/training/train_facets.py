import argparse, os, sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

print("[FACETS] import transformers/datasets ...")
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer

FACETS = ["aggression","conflict","friendliness","sexuality","success","misfortune"]

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    probs = 1/(1+np.exp(-logits))
    preds = (probs >= 0.5).astype(int)
    return {
        "f1_micro": f1_score(labels, preds, average="micro", zero_division=0),
        "f1_macro": f1_score(labels, preds, average="macro", zero_division=0),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="ml/data/facets.csv")
    ap.add_argument("--model-name", default="distilbert-base-uncased")
    ap.add_argument("--outdir", default="ml/outputs/facets_model")
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--batch-size", type:int, default=16)
    args = ap.parse_args()

    print(f"[FACETS] args={args}")
    if not os.path.exists(args.data):
        print(f"[FACETS][ERR] data not found: {args.data}", file=sys.stderr); sys.exit(2)

    df = pd.read_csv(args.data).dropna(subset=["text"]).reset_index(drop=True)
    for c in FACETS:
        if c not in df.columns:
            df[c] = 0
        df[c] = df[c].astype(int)
    print(f"[FACETS] data shape={df.shape}")

    train_df, eval_df = train_test_split(df, test_size=0.1, random_state=42)

    tok = AutoTokenizer.from_pretrained(args.model_name)
    def tokenize(ex): return tok(ex["text"], truncation=True, max_length=512)

    cols = ["text"] + FACETS
    train_ds = Dataset.from_pandas(train_df[cols]).map(tokenize, batched=True)
    eval_ds  = Dataset.from_pandas(eval_df[cols]).map(tokenize, batched=True)
    print(f"[FACETS] ds sizes: train={len(train_ds)} eval={len(eval_ds)}")

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name, num_labels=len(FACETS), problem_type="multi_label_classification"
    )

    training_args = TrainingArguments(
        output_dir=args.outdir,
        learning_rate=3e-5,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        logging_steps=25,
        report_to=[] if "report_to" in TrainingArguments.__init__.__code__.co_varnames else None,
    )

    def collator(features):
        batch = {k: [f[k] for f in features] for k in features[0].keys()}
        labels = np.array([[f[c] for c in FACETS] for f in features], dtype=np.float32)
        batch["labels"] = labels
        return tok.pad(batch, return_tensors="pt")

    print("[FACETS] start training ...")
    trainer = Trainer(
        model=model, args=training_args,
        train_dataset=train_ds, eval_dataset=eval_ds,
        tokenizer=tok, data_collator=collator,
        compute_metrics=compute_metrics,
    )
    trainer.train()

    print("[FACETS] manual evaluate ...")
    metrics = trainer.evaluate()
    print("[FACETS] eval metrics:", metrics)

    print("[FACETS] saving ...")
    trainer.save_model(args.outdir); tok.save_pretrained(args.outdir)
    print(f"[FACETS] saved to {args.outdir}")

if __name__ == "__main__":
    main()
