from pydantic import BaseModel

class ImagePrompt(BaseModel):
    prompt: str