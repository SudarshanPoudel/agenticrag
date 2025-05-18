import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

DEFAULT_LLM = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    api_key=os.getenv("GEMINI_API_KEY"), 
)