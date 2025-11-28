# backend/fastapi_app/modeltest.py
from pathlib import Path
from transformers import AutoConfig

def list_dir(p: Path):
    print(f" [list] {p}")
    if not p.exists():
        print("  -> (존재하지 않음)")
        return
    for q in sorted(p.iterdir()):
        typ = "DIR " if q.is_dir() else "FILE"
        print(f"   - {typ}: {q.name}")

def try_load(tag: str, p: Path):
    print(f"\n=== TRY LOAD: {tag} ===")
    print(" path:", p)
    print(" exists?:", p.exists())
    print(" is_dir?:", p.is_dir())
    if not p.exists():
        print(" !! 경로가 존재하지 않음")
        return
    if not (p / "config.json").exists():
        print(" !! config.json이 폴더 안에 없음")
        list_dir(p)
        return

    # 로컬 파일만 사용
    cfg = AutoConfig.from_pretrained(p, local_files_only=True)
    print(" -> LOADED OK")
    print("    model_type    :", cfg.model_type)
    print("    architectures :", getattr(cfg, "architectures", None))
    print("    name_or_path  :", getattr(cfg, "_name_or_path", None))

if __name__ == "__main__":
    # 서비스 코드와 동일한 기준: fastapi_app/.. (= backend) 밑의 ml_artifacts
    fastapi_dir = Path(__file__).resolve().parent
    backend_dir = fastapi_dir.parent
    base = (backend_dir / "ml_artifacts").resolve()

    print("[info] __file__        :", __file__)
    print("[info] fastapi_dir     :", fastapi_dir)
    print("[info] backend_dir     :", backend_dir)
    print("[info] base(artifacts) :", base)

    # 우리가 기대하는 기본 경로 점검
    for name in ["valence", "facets"]:
        p = (base / name).resolve()
        try_load(name, p)

    # 혹시 다른 위치에 있는지 전체 탐색
    print("\n=== GLOB SEARCH: **/ml_artifacts/**/config.json ===")
    root = backend_dir  # 프로젝트 루트가 다르면 여기를 Path(__file__).resolve().parents[2] 등으로 조정
    hits = list(root.glob("**/ml_artifacts/**/config.json"))
    if not hits:
        print(" (검색 결과 없음)")
    else:
        for i, hit in enumerate(hits, 1):
            print(f" [{i}] {hit}")
        # 찾은 경로들 중 상위 폴더로부터도 로딩 시도
        for hit in hits:
            try_load("FOUND", hit.parent)