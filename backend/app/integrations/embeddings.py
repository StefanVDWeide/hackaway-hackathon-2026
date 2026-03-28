from openai import AsyncOpenAI

from app.config import settings

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def generate_embedding(text: str) -> list[float]:
    """Generate a 1536-dim embedding using OpenAI text-embedding-3-large."""
    client = _get_client()
    response = await client.embeddings.create(
        input=text,
        model="text-embedding-3-large",
        dimensions=1536,
    )
    return response.data[0].embedding
