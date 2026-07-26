# backend/app/integrations/voyage_embeddings.py
"""Voyage AI embeddings client — R3 indexing."""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
BATCH_SIZE = 128


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
            json={
                "input": batch,
                "model": settings.revy_embedding_model,
                "input_type": "document",
            },
            timeout=60.0,
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
        json={
            "input": [query],
            "model": settings.revy_embedding_model,
            "input_type": "query",
        },
        timeout=60.0,
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
