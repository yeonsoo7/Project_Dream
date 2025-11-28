from fastapi import FastAPI
from fastapi_app.api import dreams as dreams_api, image as image_api, stt as stt_api
from fastapi_app.models import dream as dream_model, image as image_model
from fastapi_app.db.database import Base, engine
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
app = FastAPI(title="Dream App", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# backend/ 기준으로 generated 폴더를 가리킴
BASE_DIR = Path(__file__).resolve().parents[1]  # backend/
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")


app.include_router(dreams_api.router, prefix="/dreams", tags=["dreams"])
app.include_router(image_api.router, prefix="/images", tags=["images"])
app.include_router(stt_api.router, prefix="/stt", tags=["stt"])

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# app.include_router(dreams.router)

@app.get("/")
def root():
    return {"message": "ProjectDream API is running"}

@app.get("/health")
def health():
    return {"ok": True}