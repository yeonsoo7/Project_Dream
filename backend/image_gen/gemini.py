import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

def generate_image_from_prompt(prompt: str):
    model = genai.GenerativeModel("models/gemini-1.5-flash")

    response = model.generate_content(
        contents=prompt,
        generation_config={"temperature": 0.7},
        stream=False
    )

    image_data = response.candidates[0].content.parts[0].inline_data.data

    output_path = f"generated/dream_{hash(prompt)}.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(image_data)

    return output_path
