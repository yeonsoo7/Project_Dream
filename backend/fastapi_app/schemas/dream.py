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

class CalendarDayEmotion(BaseModel):
    date: str                  # "YYYY-MM-DD"
    avg_positive: float        # 0~1
    avg_negative: float
    score: float               # 0~1, 캘린더 색에 바로 쓰기 (0=빨강, 1=초록)
    label: str                 # "positive" / "negative" / "mixed" / "neutral"
    dream_count: int

class DreamDetail(BaseModel):
    id: int
    date: Optional[str]
    text: str
    emotion: Optional[str]
    interpretation: Optional[str]
    images: List[str]                 # 이미지 URL 리스트
    valence: Dict[str, float]        # {"positive": ..., "negative": ...}
    facets: Dict[str, float]
    nlg_notes: List[str]

    class Config:
        from_attributes = True
