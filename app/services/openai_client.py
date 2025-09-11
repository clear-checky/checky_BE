import os, httpx
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

async def chat_completion(messages, temperature=0.2, timeout=60):
    if not API_KEY:
        raise RuntimeError("OpenAI API 키가 설정되어 있지 않습니다. (.env의 OPENAI_API_KEY)")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {"model": MODEL, "messages": messages, "temperature": temperature}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(f"{BASE_URL}/chat/completions", headers=headers, json=data)
        r.raise_for_status()
        return r.json()

