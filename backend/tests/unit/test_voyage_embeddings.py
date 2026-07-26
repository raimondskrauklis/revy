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
    response.status_code = 200
    response.raise_for_status = MagicMock()
    response.json = MagicMock(return_value={"data": [{"embedding": [0.1, 0.2]}]})
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.voyage_embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = True
        mock_settings.voyage_api_key = "key"
        mock_settings.revy_embedding_model = "voyage-code-3"
        mock_settings.revy_embedding_dimensions = 1024
        vectors = await voyage_embeddings.embed_texts(client, ["hello"])

    assert vectors == [[0.1, 0.2]]
    payload = client.post.await_args.kwargs["json"]
    assert payload["model"] == "voyage-code-3"
    assert payload["output_dimension"] == 1024


@pytest.mark.asyncio
async def test_embed_texts_omits_output_dimension_for_fixed_dim_models():
    client = AsyncMock()
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status = MagicMock()
    response.json = MagicMock(return_value={"data": [{"embedding": [0.1, 0.2]}]})
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.voyage_embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = True
        mock_settings.voyage_api_key = "key"
        mock_settings.revy_embedding_model = "voyage-3-lite"
        mock_settings.revy_embedding_dimensions = 512
        await voyage_embeddings.embed_texts(client, ["hello"])

    payload = client.post.await_args.kwargs["json"]
    assert "output_dimension" not in payload


@pytest.mark.asyncio
async def test_embed_texts_raises_on_malformed_embedding_item():
    client = AsyncMock()
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status = MagicMock()
    response.json = MagicMock(return_value={"data": [{"not_embedding": True}]})
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.voyage_embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = True
        mock_settings.voyage_api_key = "key"
        mock_settings.revy_embedding_model = "voyage-code-3"
        mock_settings.revy_embedding_dimensions = 1024
        with pytest.raises(ServiceUnavailableError) as exc:
            await voyage_embeddings.embed_texts(client, ["hello"])

    assert exc.value.error_code == "embeddings_error"


@pytest.mark.asyncio
async def test_embed_texts_logs_voyage_error_body():
    client = AsyncMock()
    response = MagicMock()
    response.status_code = 400
    response.text = "Invalid model"
    response.raise_for_status = MagicMock(side_effect=Exception("400"))
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.voyage_embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = True
        mock_settings.voyage_api_key = "key"
        mock_settings.revy_embedding_model = "oyage-code-3"
        mock_settings.revy_embedding_dimensions = 1024
        with patch("app.integrations.voyage_embeddings.logger") as logger_mock:
            with pytest.raises(Exception, match="400"):
                await voyage_embeddings.embed_texts(client, ["hello"])

    logger_mock.error.assert_called_once()
    assert logger_mock.error.call_args.args[0] == "voyage_embeddings_request_failed"
