from fastapi import FastAPI
from fastapi_app.api import dreams, image
from fastapi_app.db.database import Base
from fastapi_app.db.session import engine
from fastapi_app.models import dream

from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Dream App")

app.include_router(dreams.router, prefix="/dreams", tags=["dreams"])
app.include_router(image.router, prefix="/images", tags=["images"])

@app.on_event("startup")
def on_startup():
    # 개발 단계에서는 자동 테이블 생성
    Base.metadata.create_all(bind=engine)

app.include_router(dreams.router)

@app.get("/")
def root():
    return {"message": "ProjectDream API is running"}

@app.get("/health")
def health():
    return {"ok": True}