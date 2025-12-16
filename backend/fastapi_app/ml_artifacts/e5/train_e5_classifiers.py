# fastapi_app/ml_artifacts/train_e5_classifiers.py
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import classification_report

# --------------------
# 경로 & 설정
# --------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "processed" / "e5_embeddings_labels.pt"

VALENCE_MODEL_PATH = BASE_DIR / "valence_e5_classifier.pt"
FACETS_MODEL_PATH = BASE_DIR / "facets_e5_classifier.pt"

BATCH_SIZE = 64
EPOCHS = 5
LR = 1e-3


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


def train_valence(X: torch.Tensor, y: torch.Tensor):
    print("\n=== Training valence classifier (binary) ===")

    N = X.size(0)
    indices = torch.randperm(N)
    split = int(N * 0.8)
    train_idx = indices[:split]
    test_idx = indices[split:]

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    model = MLP(768, 1)
    loss_fn = nn.BCEWithLogitsLoss()
    opt = torch.optim.Adam(model.parameters(), lr=LR)

    train_loader = DataLoader(
        TensorDataset(X_train, y_train),
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    for epoch in range(EPOCHS):
        model.train()
        for xb, yb in train_loader:
            opt.zero_grad()
            out = model(xb).squeeze(1)  # (B,)
            loss = loss_fn(out, yb)
            loss.backward()
            opt.step()

        print(f"[Valence] Epoch {epoch+1}/{EPOCHS}, loss = {loss.item():.4f}")

    # 평가
    model.eval()
    with torch.no_grad():
        logits = model(X_test).squeeze(1)
        probs = torch.sigmoid(logits)
        preds = (probs > 0.5).int()
        y_true = y_test.int()

    print("\nValence Classification Report:")
    print(
        classification_report(
            y_true.numpy(),
            preds.numpy(),
            digits=3,
            zero_division=0,
            target_names=["non_negative", "negative"],
        )
    )

    torch.save(model.state_dict(), VALENCE_MODEL_PATH)
    print("Saved valence classifier →", VALENCE_MODEL_PATH)


def train_facets(X: torch.Tensor, y: torch.Tensor):
    print("\n=== Training facets classifier (multi-label: aggr/friend/sex) ===")

    N = X.size(0)
    indices = torch.randperm(N)
    split = int(N * 0.8)
    train_idx = indices[:split]
    test_idx = indices[split:]

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    model = MLP(768, 3)
    loss_fn = nn.BCEWithLogitsLoss()
    opt = torch.optim.Adam(model.parameters(), lr=LR)

    train_loader = DataLoader(
        TensorDataset(X_train, y_train),
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    for epoch in range(EPOCHS):
        model.train()
        for xb, yb in train_loader:
            opt.zero_grad()
            out = model(xb)  # (B, 3)
            loss = loss_fn(out, yb)
            loss.backward()
            opt.step()

        print(f"[Facets] Epoch {epoch+1}/{EPOCHS}, loss = {loss.item():.4f}")

    # 평가
    model.eval()
    with torch.no_grad():
        logits = model(X_test)        # (N_test, 3)
        probs = torch.sigmoid(logits) # (N_test, 3)
        preds = (probs > 0.5).int()
        y_true = y_test.int()

    print("\nFacets Classification Report:")
    print(
        classification_report(
            y_true.numpy(),
            preds.numpy(),
            digits=3,
            zero_division=0,
            target_names=["aggr", "friend", "sex"],
        )
    )

    torch.save(model.state_dict(), FACETS_MODEL_PATH)
    print("Saved facets classifier →", FACETS_MODEL_PATH)


def main():
    print("Loading embeddings & labels...")
    data = torch.load(DATA_PATH, map_location="cpu", weights_only=False)

    X = data["embeddings"].float()   # (N, 768)
    y_val = data["valence"].float()  # (N,)
    y_fac = data["facets"].float()   # (N, 3)

    print("Shapes:")
    print("  embeddings:", X.shape)
    print("  valence:", y_val.shape)
    print("  facets:", y_fac.shape)

    train_valence(X, y_val)
    train_facets(X, y_fac)


if __name__ == "__main__":
    main()
