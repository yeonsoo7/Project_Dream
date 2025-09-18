import openai
from openai import OpenAI
import time
import os
import requests
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 OPENAI_API_KEY 불러오기
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def generate_image_from_prompt(prompt: str) -> str:
    # openai.api_key = os.getenv("OPENAI_API_KEY")

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    
    # 이미지 다운로드
    image_data = requests.get(image_url).content

    # 저장 경로 생성
    filename = f"generated/dream_{uuid4().hex}.png"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "wb") as f:
        f.write(image_data)

    return filename