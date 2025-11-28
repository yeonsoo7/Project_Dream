import os, shutil
from pathlib import Path

BASE = Path("ml/outputs")
DEST = Path("backend/fastapi_app/ml_artifacts")

def copy_model(src_name: str, dst_name: str):
    src = BASE / src_name
    dst = DEST / dst_name
    if not src.exists():
        print(f"[WARN] {src} not found, skipping.")
        return
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.glob("*"):
        if f.is_file():
            shutil.copy(f, dst / f.name)
    print(f"[OK] Copied {src_name} → {dst_name}")

def main():
    copy_model("valence_model", "valence")
    copy_model("facets_model", "facets")

if __name__ == "__main__":
    main()
