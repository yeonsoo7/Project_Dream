from fastapi import FastAPI
from backend.api import dreams, image
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

app.include_router(dreams.router, prefix="/dreams", tags=["dreams"])
app.include_router(image.router, prefix="/images", tags=["images"])


@app.get("/")
def root():
    return {"message": "ProjectDream API is running"}
