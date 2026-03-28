"""Tests for the OpenAI embeddings integration.

Unit tests mock the OpenAI client.
Integration tests (marked with `pytest.mark.integration`) call the real API.
Run integration tests with: pytest -m integration
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Unit tests (mocked)
# ---------------------------------------------------------------------------


async def test_generate_embedding_calls_openai():
    """Verify generate_embedding calls the client with correct params."""
    fake_embedding = [0.5] * 1536
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=fake_embedding)]

    mock_client = AsyncMock()
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)

    with patch(
        "app.integrations.embeddings._get_client", return_value=mock_client
    ):
        from app.integrations.embeddings import generate_embedding

        result = await generate_embedding("Hello world")

    assert result == fake_embedding
    mock_client.embeddings.create.assert_called_once_with(
        input="Hello world",
        model="text-embedding-3-large",
        dimensions=1536,
    )


async def test_generate_embedding_returns_list_of_floats():
    fake_embedding = [0.1, 0.2, 0.3]
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=fake_embedding)]

    mock_client = AsyncMock()
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)

    with patch(
        "app.integrations.embeddings._get_client", return_value=mock_client
    ):
        from app.integrations.embeddings import generate_embedding

        result = await generate_embedding("test")

    assert isinstance(result, list)
    assert all(isinstance(x, float) for x in result)


# ---------------------------------------------------------------------------
# Integration tests (real OpenAI API — requires OPENAI_API_KEY env var)
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_real_embedding_generation():
    """Integration test: calls the real OpenAI API.

    Run with: pytest -m integration
    Requires OPENAI_API_KEY to be set.
    """
    # Reset the cached client so it picks up the real API key
    import app.integrations.embeddings as mod

    mod._client = None

    from app.integrations.embeddings import generate_embedding

    result = await generate_embedding(
        "A vintage mechanical keyboard in excellent condition"
    )

    assert isinstance(result, list)
    assert len(result) == 1536
    assert all(isinstance(x, float) for x in result)


@pytest.mark.integration
async def test_real_embedding_different_texts_differ():
    """Integration test: different texts should produce different embeddings."""
    import app.integrations.embeddings as mod

    mod._client = None

    from app.integrations.embeddings import generate_embedding

    emb1 = await generate_embedding("mechanical keyboard")
    emb2 = await generate_embedding("fresh organic bananas")

    assert emb1 != emb2
