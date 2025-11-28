import argparse, json
import numpy as np
import pandas as pd
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
import torch
from sklearn.metrics import f1_score

ALL_FACETS = ["aggression","conflict","friendliness","sexuality","success","misfortune"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--model-name", default="roberta-base")
    ap.add_argument("--outdir", default="ml/outputs/facets_model")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=16)
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    # 1) 활성 레이블만 사용
    pos_counts = {c: int(df[c].sum()) if c in df.columns else 0 for c in ALL_FACETS}
    ACTIVE_LABELS = [c for c, n in pos_counts.items() if n > 0]
    if not ACTIVE_LABELS:
        raise RuntimeError("No positive labels found in any facet. Check your dataset.")
    print("[FACETS] positive counts:", pos_counts)
    print("[FACETS] ACTIVE_LABELS:", ACTIVE_LABELS)

    dataset = Dataset.from_pandas(df)
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def preprocess(example):
        out = tokenizer(example["text"], truncation=True, padding="max_length", max_length=128)
        out["labels"] = [float(example[c]) for c in ACTIVE_LABELS]
        return out

    dataset = dataset.map(preprocess)
    dataset = dataset.remove_columns([c for c in dataset.column_names if c not in ["input_ids","attention_mask","labels"]])
    dataset = dataset.train_test_split(test_size=0.1, seed=42)
    print("[FACETS] ds sizes: train=", len(dataset["train"]), "eval=", len(dataset["test"]))

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=len(ACTIVE_LABELS),
        problem_type="multi_label_classification",
    )

    def collator(features):
        batch = tokenizer.pad([{k: v for k, v in f.items() if k != "labels"} for f in features], return_tensors="pt")
        batch["labels"] = torch.tensor([f["labels"] for f in features], dtype=torch.float32)
        return batch

    def compute_metrics(pred):
        probs = torch.sigmoid(torch.tensor(pred.predictions))
        preds = (probs > 0.5).int().numpy()
        labels = pred.label_ids
        per_f1 = []
        for i in range(len(ACTIVE_LABELS)):
            per_f1.append(f1_score(labels[:, i], preds[:, i], zero_division=0))
        return {"f1_macro": float(np.mean(per_f1))}

    training_args = TrainingArguments(
        output_dir=args.outdir,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        report_to="none",
        logging_steps=50,
        learning_rate=2e-5,
        weight_decay=0.01,
        fp16=True,  # GPU에서 더 빠르게 (CUDA일 때만 적용)
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        tokenizer=tokenizer,
        data_collator=collator,
        compute_metrics=compute_metrics,
    )

    print("[FACETS] start training ...")
    trainer.train()
    metrics = trainer.evaluate()
    print("[FACETS] eval metrics:", metrics)

    # 2) 라벨 목록 저장 (추론 시 맵핑에 사용)
    import os
    os.makedirs(args.outdir, exist_ok=True)
    with open(f"{args.outdir}/labels.json", "w", encoding="utf-8") as f:
        json.dump({"labels": ACTIVE_LABELS}, f, ensure_ascii=False, indent=2)

    trainer.save_model(args.outdir)
    print("[FACETS] saved to", args.outdir)

if __name__ == "__main__":
    main()
