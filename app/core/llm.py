import os
from langchain_openai import ChatOpenAI

from app.core import load_app_env

load_app_env()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """
    Mengembalikan LLM instance yang terhubung ke OpenRouter.
    OpenRouter kompatibel dengan OpenAI SDK — cukup ganti base_url dan api_key.
    """
    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        temperature=temperature,
        default_headers={
            "HTTP-Referer": "https://healthy-ai.app",
            "X-Title": "Healthy AI",
        },
    )
