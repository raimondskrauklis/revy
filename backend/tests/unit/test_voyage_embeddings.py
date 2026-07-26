# backend/tests/unit/test_voyage_embeddings.py
"""Voyage embeddings client — R3."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ServiceUnavailableError
from app.integrations import voyage_embeddings


@pytest.mark.asyncio
async def test_embed_texts_disabled_raises():
    client = AsyncMock()
    with patch("app.integrations.voyage_embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = False
        with pytest.raises(ServiceUnavailableError) as exc:
            await voyage_embeddings.embed_texts(client, ["hello"])
    assert exc.value.error_code == "embeddings_disabled"


@pytest.mark.asyncio
async def test_embed_texts_returns_vectors():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json = MagicMock(return_value={"data": [{"embedding": [0.1, 0.2]}]})
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.voyage_embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = True
        mock_settings.voyage_api_key = "key"
        mock_settings.revy_embedding_model = "voyage-3-lite"
        vectors = await voyage_embeddings.embed_texts(client, ["hello"])

    assert vectors == [[0.1, 0.2]]
