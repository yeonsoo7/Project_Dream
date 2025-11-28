from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# -----------------------------
# 1. 경로 설정
#    - 이 파일 위치: backend/fastapi_app/db/database.py
#    - parents[0] = .../fastapi_app/db
#    - parents[1] = .../fastapi_app
#    - parents[2] = .../backend
# -----------------------------
CURRENT_FILE = Path(__file__).resolve()
FASTAPI_DIR = CURRENT_FILE.parents[1]   # fastapi_app
BACKEND_DIR = CURRENT_FILE.parents[2]   # backend

# -----------------------------
# 2. .env 로드 (backend/.env)
# -----------------------------
env_path = BACKEND_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

# -----------------------------
# 3. DB URL 설정
#    - DATABASE_URL 있으면 그걸 사용 (PostgreSQL 등)
#    - 없으면 fastapi_app/app.db 로 SQLite 사용
# -----------------------------
DEFAULT_SQLITE = f"sqlite:///{(BACKEND_DIR / 'app.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE)

# SQLite일 경우만 connect_args 필요
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -----------------------------
# 4. FastAPI에서 쓸 의존성 함수
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
