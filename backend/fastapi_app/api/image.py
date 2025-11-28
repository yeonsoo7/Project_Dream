from fastapi import APIRouter, Request
from fastapi_app.image_gen.schema import ImagePrompt
from fastapi_app.image_gen.openai_dalle import generate_image_from_prompt
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
# from uuid import uuid4

router = APIRouter(prefix="/image", tags=["image"])

class ImageGenReq(BaseModel):
    prompt: str

class ImageGenResp(BaseModel):
    image_url: str

class ImageMeta(BaseModel):
    prompt: str
    image_path: str
    created_at: datetime


@router.post("/generate", response_model=ImageGenResp)
def generate(req: ImageGenReq, request: Request):
    # # 파일명에 UUID 적용
    # name = f"dream_{uuid4().hex}.png"
    # out_path = Path("generated") / name
    
    # import shutil
    # sample = Path("fastapi_app/image_gen/sample.png")
    # shutil.copy(sample, out_path)

    # # 절대 URL 생성
    # base = str(request.base_url).rstrip("/")
    # abs_url = f"{base}/{out_path.as_posix()}"
    # return ImageGenResp(image_url=abs_url)
    try:
        # DALL·E 호출 → 파일 경로 반환
        out_path = Path(generate_image_from_prompt(req.prompt))  # e.g. "generated/dream_xxx.png"

        # 절대 URL 생성
        base = str(request.base_url).rstrip("/")
        abs_url = f"{base}/{out_path.as_posix()}"

        return ImageGenResp(image_url=abs_url)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")