from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.database import Base

class Dream(Base):
    __tablename__ = "dreams"

    id = Column(Integer, primary_key=True, index=True)
    input_type = Column(String, nullable=False)  # "voice" or "text"
    input_text = Column(Text, nullable=False)
    stt_text = Column(Text)  # 음성을 텍스트로 바꾼 경우
    emotion = Column(String)
    interpretation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    images = relationship("Image", back_populates="dream", cascade="all, delete")
