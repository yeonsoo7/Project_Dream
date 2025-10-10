from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Float, func
from sqlalchemy.orm import relationship
from datetime import datetime

from fastapi_app.db.database import Base

class Dream(Base):
    __tablename__ = "dreams"

    id = Column(Integer, primary_key=True, index=True)
    input_type = Column(String(20), nullable=False)  # "voice" or "text"
    input_text = Column(Text, nullable=True)
    stt_text = Column(Text, nullable=True)  # 음성을 텍스트로 바꾼 경우
    text = Column(Text, nullable=False)
    # 선택적 메타
    emotion = Column(String(50), nullable=True) # 사용자가 기입한 감정
    interpretation = Column(Text, nullable=True) # 사용자가 기입한 해석
    user_id = Column(String(64), index=True, nullable=True)
    date = Column(String(10), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    images = relationship("Image", back_populates="dream", cascade="all, delete")

    # 관계
    analyses = relationship("DreamAnalysis", back_populates="dream", cascade="all, delete-orphan")

class DreamAnalysis(Base):
    __tablename__ = "dream_analyses"

    id = Column(Integer, primary_key=True, index=True)
    dream_id = Column(Integer, ForeignKey("dreams.id", ondelete="CASCADE"), nullable=False)

    # 긍/부정 확률
    pos_prob = Column(Float, nullable=False)
    neg_prob = Column(Float, nullable=False)

    # 세부 요소 및 노트
    facets_json = Column(JSON, nullable=False, default={})
    notes_json = Column(JSON, nullable=False, default=[])

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 관계
    dream = relationship("Dream", back_populates="analyses")

    @classmethod
    def from_result(cls, dream_id: int, result: dict) -> "DreamAnalysis":
        return cls(
            dream_id=dream_id,
            pos_prob=float(result["valence"]["positive"]),
            neg_prob=float(result["valence"]["negative"]),
            facets_json=result.get("facets", {}),
            notes_json=result.get("nlg_notes", []),
        )