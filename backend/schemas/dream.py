# 요청/응답용 Pydantic 모델

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DreamCreate(BaseModel):
    input_type: str  # "text" or "voice"
    input_text: str
    stt_text: Optional[str] = None
    emotion: Optional[str] = None
    interpretation: Optional[str] = None

class DreamResponse(DreamCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
