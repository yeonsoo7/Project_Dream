# 실제 API 로직
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from typing import Optional
from fastapi_app.schemas.dream import DreamCreate, DreamResponse
from fastapi_app.services.dream_analyzer import DreamAnalyzer
from fastapi_app.db.session import get_db
from fastapi_app.models.dream import Dream, DreamAnalysis


router = APIRouter(prefix="/dreams", tags=["dreams"])


@router.post("/", response_model=DreamResponse)
def create_dream(dream: DreamCreate, db: Session = Depends(get_db)):
    db_dream = Dream(**dream.dict())
    db.add(db_dream)
    db.commit()
    db.refresh(db_dream)
    return db_dream


class AnalyzeReq(BaseModel):
    text: str
    user_id: Optional[str] = None
    date: Optional[str] = None  # "YYYY-MM-DD"

@router.post("/analyze")
def analyze(req: AnalyzeReq, db: Session = Depends(get_db)):
    res = DreamAnalyzer.get().analyze(req.text)

    # (선택) DB 저장
    dream = Dream(user_id=req.user_id, text=req.text, date=req.date)
    db.add(dream); db.flush()

    analysis = DreamAnalysis.from_result(dream_id=dream.id, result=res)
    db.add(analysis); db.commit(); db.refresh(analysis)

    res["dream_id"] = dream.id
    res["saved_analysis_id"] = analysis.id
    return res