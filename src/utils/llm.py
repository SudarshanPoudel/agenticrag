import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

DEFAULT_LLM = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro", 
    api_key=os.getenv("GEMINI_API_KEY"), 
    temperature=0.3
)