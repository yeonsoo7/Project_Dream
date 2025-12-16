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
            language="ko",
            vad_filter=True,
            beam_size=3,
            temperature=0.0,
        )
        text = "".join(s.text for s in segments).strip()
        return SttResp(text=text, duration_sec=getattr(info, "duration", None))
    finally:
        try: os.unlink(path)
        except: pass
