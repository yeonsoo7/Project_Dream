from fastapi import FastAPI
from backend.api import dreams

app = FastAPI()

app.include_router(dreams.router, prefix="/dreams", tags=["dreams"])

@app.get("/")
def root():
    return {"message": "ProjectDream API is running"}
