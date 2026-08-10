# backend/scripts/voyage_code_4_smoke_test.py
"""Smoke-test Voyage embedding models — voyage-code-3 vs code-4 series."""
from __future__ import annotations

import argparse
import asyncio
import json
import math
from dataclasses import dataclass

import httpx

from app.core.config import settings

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
DEFAULT_SAMPLE = 'def fetch_user(user_id: int) -> dict:\n    return {"id": user_id}\n'
DEFAULT_MODELS = (
    "voyage-code-3",
    "voyage-code-4",
    "voyage-code-4-large",
)


@dataclass(frozen=True)
class ModelProbeResult:
    model: str
    ok: bool
    status_code: int | None
    dimension: int | None
    total_tokens: int | None
    error: str | None
    embedding_head: list[float] | None
    embedding: list[float] | None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Voyage code embedding model smoke test")
    parser.add_argument(
        "--models",
        nargs="+",
        default=list(DEFAULT_MODELS),
        help="Model ids to probe (default: voyage-code-3 voyage-code-4 voyage-code-4-large)",
    )
    parser.add_argument(
        "--dimension",
        type=int,
        default=None,
        help="output_dimension (default: REVY_EMBEDDING_DIMENSIONS or 1024)",
    )
    parser.add_argument(
        "--sample",
        default=DEFAULT_SAMPLE,
        help="Code sample to embed",
    )
    return parser.parse_args()


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError(f"dimension mismatch: {len(left)} vs {len(right)}")
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _flexible_dimension_model(model: str) -> bool:
    normalized = model.strip().lower()
    prefixes = (
        "voyage-code-3",
        "voyage-code-4",
        "voyage-4",
        "voyage-3-large",
        "voyage-3.5",
    )
    return any(normalized.startswith(prefix) for prefix in prefixes)


async def _probe_model(
    client: httpx.AsyncClient,
    *,
    api_key: str,
    model: str,
    sample: str,
    dimension: int,
) -> ModelProbeResult:
    body: dict[str, object] = {
        "input": [sample],
        "model": model,
        "input_type": "document",
    }
    if _flexible_dimension_model(model):
        body["output_dimension"] = dimension

    try:
        response = await client.post(
            VOYAGE_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=60.0,
        )
    except httpx.HTTPError as exc:
        return ModelProbeResult(
            model=model,
            ok=False,
            status_code=None,
            dimension=None,
            total_tokens=None,
            error=str(exc),
            embedding_head=None,
            embedding=None,
        )

    if response.status_code != 200:
        detail = response.text.strip()
        if len(detail) > 500:
            detail = detail[:500] + "..."
        return ModelProbeResult(
            model=model,
            ok=False,
            status_code=response.status_code,
            dimension=None,
            total_tokens=None,
            error=detail or f"HTTP {response.status_code}",
            embedding_head=None,
            embedding=None,
        )

    payload = response.json()
    items = payload.get("data")
    if not isinstance(items, list) or not items:
        return ModelProbeResult(
            model=model,
            ok=False,
            status_code=response.status_code,
            dimension=None,
            total_tokens=None,
            error="response missing data[]",
            embedding_head=None,
            embedding=None,
        )
    first = items[0]
    embedding = first.get("embedding") if isinstance(first, dict) else None
    if not isinstance(embedding, list) or not embedding:
        return ModelProbeResult(
            model=model,
            ok=False,
            status_code=response.status_code,
            dimension=None,
            total_tokens=None,
            error="response missing embedding vector",
            embedding_head=None,
            embedding=None,
        )

    vector = [float(value) for value in embedding]

    usage = payload.get("usage")
    total_tokens = None
    if isinstance(usage, dict) and isinstance(usage.get("total_tokens"), int):
        total_tokens = usage["total_tokens"]

    return ModelProbeResult(
        model=model,
        ok=True,
        status_code=response.status_code,
        dimension=len(vector),
        total_tokens=total_tokens,
        error=None,
        embedding_head=vector[:5],
        embedding=vector,
    )


def _print_config(dimension: int) -> None:
    print("Voyage embedding smoke test")
    print(f"  embeddings enabled: {settings.embeddings_enabled}")
    print(f"  configured model: {settings.revy_embedding_model}")
    print(f"  configured dimensions: {settings.revy_embedding_dimensions}")
    print(f"  probe dimension: {dimension}")


def _print_result(result: ModelProbeResult) -> None:
    status = "OK" if result.ok else "FAIL"
    print(f"\n--- {result.model} [{status}] ---")
    if result.status_code is not None:
        print(f"  status: {result.status_code}")
    if result.dimension is not None:
        print(f"  dimension: {result.dimension}")
    if result.total_tokens is not None:
        print(f"  total_tokens: {result.total_tokens}")
    if result.embedding_head is not None:
        print(f"  embedding[:5]: {result.embedding_head}")
    if result.error:
        print(f"  error: {result.error}")


async def _run() -> int:
    args = _parse_args()
    dimension = args.dimension or settings.revy_embedding_dimensions or 1024
    _print_config(dimension)

    api_key = settings.voyage_api_key
    if not api_key or not api_key.strip():
        print("VOYAGE_API_KEY is not configured")
        return 1

    embeddings: dict[str, list[float]] = {}
    results: list[ModelProbeResult] = []

    async with httpx.AsyncClient() as client:
        for model in args.models:
            result = await _probe_model(
                client,
                api_key=api_key.strip(),
                model=model,
                sample=args.sample,
                dimension=dimension,
            )
            results.append(result)
            _print_result(result)
            if result.ok and result.embedding is not None:
                embeddings[model] = result.embedding

    ok_models = [result.model for result in results if result.ok]
    if len(ok_models) >= 2:
        print("\n--- cosine similarity (same input) ---")
        base = ok_models[0]
        for other in ok_models[1:]:
            left = embeddings.get(base)
            right = embeddings.get(other)
            if left is None or right is None:
                continue
            similarity = _cosine_similarity(left, right)
            print(f"  {base} vs {other}: {similarity:.6f}")

    if len(embeddings) >= 2 and "voyage-code-4" in embeddings and "voyage-code-4-large" in embeddings:
        similarity = _cosine_similarity(
            embeddings["voyage-code-4"],
            embeddings["voyage-code-4-large"],
        )
        print(f"  voyage-code-4 vs voyage-code-4-large: {similarity:.6f}")

    summary = {
        "dimension": dimension,
        "results": [
            {
                "model": result.model,
                "ok": result.ok,
                "status_code": result.status_code,
                "dimension": result.dimension,
                "total_tokens": result.total_tokens,
                "error": result.error,
            }
            for result in results
        ],
    }
    print("\nJSON summary:")
    print(json.dumps(summary, indent=2))

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
