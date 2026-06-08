from openai import OpenAI
from api.app.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_embedding(text: str) -> list[float]:

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
    )

    return response.data[0].embedding