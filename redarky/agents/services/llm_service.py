from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from api.app.config import settings


class LLMService:

    @staticmethod
    def get_openai():
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.3,
        )

    @staticmethod
    def get_gemini():
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
        )