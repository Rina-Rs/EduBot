from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
import os

BASE_DIR = Path.cwd()

load_dotenv(BASE_DIR / ".env")

key = os.getenv("OPENROUTER_API_KEY")

print("Clé présente :", bool(key))
print("Préfixe :", key[:9] if key else None)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=key,
)

response = client.chat.completions.create(
    model="openrouter/free",
    messages=[
        {
            "role": "user",
            "content": "Bonjour, réponds simplement OK."
        }
    ],
)

print(response.choices[0].message.content)