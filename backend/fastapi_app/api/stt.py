# # --- ultra-light CPU setup ---
# import os
# from pathlib import Path
# os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
# os.environ["HF_HOME"] = str(Path(__file__).parent / ".hf_cache")
# os.environ["CT2_USE_MMAP"] = "1"   # 메모리 매핑으로 로딩 부담 완화
# os.environ["CT2_THREADS"] = "2"    # 내부 스레드 제한(과열 완화)

# from fastapi import FastAPI, UploadFile, File
# from pydantic import BaseModel
# import tempfile, shutil

# app = FastAPI()

# @app.get("/ping")
# def ping():
#     return {"ok": True}

# class SttResp(BaseModel):
#     text: str
#     duration_sec: float | None = None

# model = None
# def get_model():
#     global model
#     if model is None:
#         # ✅ 더 가벼운 모델로 변경: "tiny" (테스트용), 필요 시 "base"
#         from faster_whisper import WhisperModel
#         model = WhisperModel(
#             "tiny",                 # "base"도 가능, "small"은 무거움
#             device="cpu",
#             compute_type="int8",    # CPU 최적
#             cpu_threads=2           # CPU 점유 낮추기
#         )
#         print(">> WhisperModel(tiny/int8) loaded with 2 threads")
#     return model

# @app.post("/stt", response_model=SttResp)
# async def stt(file: UploadFile = File(...)):
#     m = get_model()
#     with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
#         shutil.copyfileobj(file.file, tmp)
#         path = tmp.name

#     segments, info = m.transcribe(
#         path,
#         language="ko",
#         vad_filter=True,
#         beam_size=3,
#         temperature=0.0
#     )
#     text = "".join(seg.text for seg in segments).strip()
#     return SttResp(text=text, duration_sec=getattr(info, "duration", None))

# fastapi_app/api/stt.py
import os
from pathlib import Path
import tempfile, shutil

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

# ---- 환경 변수 (윈도우/저사양 안정화) ----
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
HF_HOME_DIR = Path(__file__).resolve().parents[1].parent / ".hf_cache"  # backend/.hf_cache
os.environ.setdefault("HF_HOME", str(HF_HOME_DIR))
os.environ.setdefault("CT2_USE_MMAP", "1")
os.environ.setdefault("CT2_THREADS", "2")

router = APIRouter(prefix="/stt", tags=["stt"])

# 지연 로딩
_model = None
def get_model():
    global _model
    if _model is None:
        # 로컬 CPU 기본 (가벼운 tiny/int8). GPU 사용 시 아래 두 줄로 바꿔도 됨.
        from faster_whisper import WhisperModel
        device = os.getenv("STT_DEVICE", "cpu")          # "cpu" | "cuda"
        ctype  = os.getenv("STT_COMPUTE", "int8")        # cpu:int8, cuda:float16
        size   = os.getenv("STT_MODEL_SIZE", "tiny")     # tiny/base/small …
        _model = WhisperModel(size, device=device, compute_type=ctype, cpu_threads=int(os.getenv("CT2_THREADS","2")))
        print(f">> STT loaded: size={size}, device={device}, compute={ctype}")
    return _model

class SttResp(BaseModel):
    text: str
    duration_sec: float | None = None

@router.post("", response_model=SttResp)  # POST /stt
async def transcribe(file: UploadFile = File(...)):
    m = get_model()
    # 업로드 파일 임시 저장
    with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        path = tmp.name

    try:
        segments, info = m.transcribe(
            path,
            language="ko",          # 자동감지 원하면 None
            vad_filter=True,
            beam_size=3,
            temperature=0.0,
        )
        text = "".join(s.text for s in segments).strip()
        return SttResp(text=text, duration_sec=getattr(info, "duration", None))
    finally:
        try: os.unlink(path)
        except: pass
