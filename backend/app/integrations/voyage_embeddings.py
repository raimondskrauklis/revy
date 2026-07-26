# backend/app/integrations/voyage_embeddings.py
"""Voyage AI embeddings client — R3 indexing."""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
BATCH_SIZE = 128
_FLEXIBLE_DIMENSION_MODEL_PREFIXES = (
    "voyage-code-3",
    "voyage-4",
    "voyage-3-large",
    "voyage-3.5",
)


def _model_supports_output_dimension(model: str) -> bool:
    normalized = model.strip().lower()
    return any(normalized.startswith(prefix) for prefix in _FLEXIBLE_DIMENSION_MODEL_PREFIXES)


def _embedding_request_body(texts: list[str], *, input_type: str) -> dict[str, object]:
    body: dict[str, object] = {
        "input": texts,
        "model": settings.revy_embedding_model,
        "input_type": input_type,
    }
    if _model_supports_output_dimension(settings.revy_embedding_model):
        body["output_dimension"] = settings.revy_embedding_dimensions
    return body


def _require_embeddings_enabled() -> None:
    if not settings.embeddings_enabled:
        raise ServiceUnavailableError(
            message="Embeddings API is not configured",
            error_code="embeddings_disabled",
        )


async def embed_texts(
    client: httpx.AsyncClient,
    texts: list[str],
) -> list[list[float]]:
    _require_embeddings_enabled()
    if not texts:
        return []

    api_key = settings.voyage_api_key
    if not api_key:
        raise ServiceUnavailableError(
            message="Embeddings API is not configured",
            error_code="embeddings_disabled",
        )

    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        response = await client.post(
            VOYAGE_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=_embedding_request_body(batch, input_type="document"),
            timeout=60.0,
        )
        if response.status_code >= 400:
            logger.error(
                "voyage_embeddings_request_failed",
                extra={
                    "status_code": response.status_code,
                    "model": settings.revy_embedding_model,
                    "body": response.text[:2000],
                },
            )
        response.raise_for_status()
        data = response.json()
        items = data.get("data")
        if not isinstance(items, list):
            raise ServiceUnavailableError(
                message="Voyage embeddings response invalid",
                error_code="embeddings_error",
            )
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("embedding"), list):
                vectors.append(item["embedding"])
                continue
            raise ServiceUnavailableError(
                message="Voyage embeddings response invalid",
                error_code="embeddings_error",
            )
    return vectors


async def embed_query(client: httpx.AsyncClient, query: str) -> list[float]:
    _require_embeddings_enabled()
    api_key = settings.voyage_api_key
    if not api_key:
        raise ServiceUnavailableError(
            message="Embeddings API is not configured",
            error_code="embeddings_disabled",
        )

    response = await client.post(
        VOYAGE_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=_embedding_request_body([query], input_type="query"),
        timeout=60.0,
    )
    if response.status_code >= 400:
        logger.error(
            "voyage_embeddings_request_failed",
            extra={
                "status_code": response.status_code,
                "model": settings.revy_embedding_model,
                "body": response.text[:2000],
            },
        )
    response.raise_for_status()
    data = response.json()
    items = data.get("data")
    if not isinstance(items, list) or not items:
        raise ServiceUnavailableError(
            message="Voyage embeddings response invalid",
            error_code="embeddings_error",
        )
    embedding = items[0].get("embedding") if isinstance(items[0], dict) else None
    if not isinstance(embedding, list):
        raise ServiceUnavailableError(
            message="Voyage embeddings response invalid",
            error_code="embeddings_error",
        )
    return embedding
