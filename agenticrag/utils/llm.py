# utils/llm.py

import os
from dotenv import load_dotenv

from agenticrag.core import LLMClient
load_dotenv()

def get_default_llm():
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set in your environment.\n"
            "To use the default LLM (Gemini), please set GEMINI_API_KEY in your .env or environment variables.\n"
            "Alternatively, pass a custom LLM (any instance of `BaseChatModel` from `langchain_core` is supported)."
        )

    return LLMClient(
        model="gemini-2.0-flash",
        api_key=gemini_api_key,
    )
