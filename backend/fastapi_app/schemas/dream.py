# 요청/응답용 Pydantic 모델

from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class DreamCreate(BaseModel):
    input_type: str  # "text" or "voice"
    input_text: str
    stt_text: Optional[str] = None
    emotion: Optional[str] = None
    interpretation: Optional[str] = None
    user_id: Optional[str] = None
    date: Optional[str] = None
    text: str

class DreamResponse(DreamCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DreamAnalyzeRes(BaseModel):
    valence: Dict[str, float]
    facets: Dict[str, float]
    evidence: Dict[str, List[dict]]
    nlg_notes: List[str]
    dream_id: Optional[int] = None
    saved_analysis_id: Optional[int] = None