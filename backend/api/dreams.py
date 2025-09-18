# 실제 API 로직
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas.dream import DreamCreate, DreamResponse
from backend.models.dream import Dream
from backend.deps.db import get_db

router = APIRouter()

@router.post("/", response_model=DreamResponse)
def create_dream(dream: DreamCreate, db: Session = Depends(get_db)):
    db_dream = Dream(**dream.dict())
    db.add(db_dream)
    db.commit()
    db.refresh(db_dream)
    return db_dream
