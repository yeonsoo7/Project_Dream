from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from fastapi_app.db.session import get_db
from fastapi_app.services.dream_analyzer import DreamAnalyzer
from fastapi_app.services.dream_counselor import counseling_note
from fastapi_app.models.dream import Dream, DreamAnalysis
from fastapi_app.models.image import Image
from fastapi_app.schemas.dream import DreamAnalyzeRes, CalendarDayEmotion, DreamDetail
from fastapi_app.services.dream_analyzer import analyze_dream_with_e5


router = APIRouter(tags=["dreams"])

class AnalyzeReq(BaseModel):
    text: str
    user_id: Optional[str] = None
    date: Optional[str] = None  # "YYYY-MM-DD"

@router.post("/analyze")
def analyze(req: AnalyzeReq, db: Session = Depends(get_db)):
    res = DreamAnalyzer.get().analyze(req.text)

    # 날짜 기본값: 요청에 없으면 오늘 날짜
    date_str = req.date or datetime.now().date().isoformat()

    # user_id 기본값: 요청에 없으면 "test_user" (지금 앱에서 쓰는 값이랑 맞춰둠)
    user_id = req.user_id or "test_user"

    # Dream 필수 필드 채워 저장
    dream = Dream(
        user_id=user_id,
        text=req.text,
        input_type="text",
        input_text=req.text,
        date=date_str,
    )
    db.add(dream)
    db.flush()  # dream.id 확보

    analysis = DreamAnalysis.from_result(dream_id=dream.id, result=res)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    res["dream_id"] = dream.id
    res["saved_analysis_id"] = analysis.id
    res["counseling_note"] = counseling_note(
        req.text,
        res["valence"],
        res["facets"]["probs"],  # ← 확률 dict만 전달
    )

    return res

@router.get("/calendar", response_model=List[CalendarDayEmotion])
def get_calendar_emotions(
    user_id: str,
    month: str,  # "2025-11" 이런 형태
    db: Session = Depends(get_db),
):
    """
    특정 유저의 특정 month(YYYY-MM)에 대해
    날짜별 감정 평균을 캘린더용으로 반환.
    """

    like_pattern = f"{month}-%"  # "2025-11-%"

    q = (
        db.query(
            Dream.date.label("date"),
            func.avg(DreamAnalysis.pos_prob).label("avg_pos"),
            func.avg(DreamAnalysis.neg_prob).label("avg_neg"),
            func.count(Dream.id).label("dream_count"),
        )
        .join(DreamAnalysis, DreamAnalysis.dream_id == Dream.id)
        .filter(Dream.user_id == user_id)
        .filter(Dream.date.like(like_pattern))
        .group_by(Dream.date)
        .order_by(Dream.date)
    )

    rows = q.all()
    result: List[CalendarDayEmotion] = []

    for r in rows:
        avg_pos = float(r.avg_pos or 0.0)
        avg_neg = float(r.avg_neg or 0.0)

        # 간단한 라벨링 규칙
        if avg_pos >= 0.6 and avg_neg <= 0.4:
            label = "positive"
        elif avg_neg >= 0.6 and avg_pos <= 0.4:
            label = "negative"
        elif abs(avg_pos - avg_neg) < 0.15:
            label = "mixed"
        else:
            label = "neutral"

        result.append(
            CalendarDayEmotion(
                date=r.date,
                avg_positive=avg_pos,
                avg_negative=avg_neg,
                score=avg_pos,  # 0(빨강) ~ 1(초록)로 쓰면 됨
                label=label,
                dream_count=r.dream_count,
            )
        )

    return result

@router.get("/by-date", response_model=List[DreamDetail])
def get_dreams_by_date(
    user_id: str,
    date: str,  # "YYYY-MM-DD"
    db: Session = Depends(get_db),
):
    """
    특정 유저의 특정 날짜에 해당하는 모든 꿈 + 분석 + 이미지들을 반환.
    """
    dreams = (
        db.query(Dream)
        .filter(Dream.user_id == user_id)
        .filter(Dream.date == date)
        .all()
    )

    result: List[DreamDetail] = []

    for d in dreams:
        # 분석은 꿈당 1개라고 가정, 여러 개면 마지막(최신) 사용
        analysis = d.analyses[-1] if d.analyses else None

        if analysis:
            valence = {
                "positive": float(analysis.pos_prob),
                "negative": float(analysis.neg_prob),
            }
            facets = dict(analysis.facets_json or {})
            nlg_notes = list(analysis.notes_json or [])
        else:
            valence = {"positive": 0.5, "negative": 0.5}
            facets = {}
            nlg_notes = []

        # Image 모델의 image_url 필드 그대로 사용
        image_urls = []
        for img in d.images:
            # DB에는 "generated/xxx.png" 이런 식으로 저장된다고 가정
            # 안드로이드에서 전체 URL로 만들면 됨
            image_urls.append("/" + img.image_url.lstrip("/"))

        result.append(
            DreamDetail(
                id=d.id,
                date=d.date,
                text=d.text,
                emotion=d.emotion,
                interpretation=d.interpretation,
                images=image_urls,
                valence=valence,
                facets=facets,
                nlg_notes=nlg_notes,
            )
        )

    return result
