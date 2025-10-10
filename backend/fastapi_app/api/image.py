from fastapi import APIRouter
from fastapi_app.image_gen.schema import ImagePrompt
from fastapi_app.image_gen.openai_dalle import generate_image_from_prompt

router = APIRouter()

@router.post("/generate-image")
def generate_image(prompt: ImagePrompt):
    image_path = generate_image_from_prompt(prompt.prompt)
    return {"image_path": image_path}