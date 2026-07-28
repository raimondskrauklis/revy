# backend/app/integrations/llm_dispatch.py
"""LLM provider dispatch — MODEL_POLICY M0."""
from __future__ import annotations

import httpx

from app.constants.model_registry import SUPPORTED_JUDGE_PROVIDERS
from app.core.exceptions import ServiceUnavailableError
from app.integrations import anthropic_review, bedrock_review, moonshot_review
from app.services.model_policy import ModelRef


async def call_review_llm(
    client: httpx.AsyncClient,
    *,
    model_ref: ModelRef,
    profile: str,
    user_prompt: str,
    timeout_seconds: float,
) -> str:
    provider = model_ref.provider.strip().lower()
    if provider == "anthropic":
        return await anthropic_review.complete_review(
            client,
            user_prompt=user_prompt,
            model_id=model_ref.model_id,
            timeout_seconds=timeout_seconds,
        )
    if provider == "moonshot":
        return await moonshot_review.complete_review(
            client,
            profile=profile,
            user_prompt=user_prompt,
            model_id=model_ref.model_id,
            timeout_seconds=timeout_seconds,
        )
    if provider == "bedrock":
        return await bedrock_review.complete_review(
            user_prompt=user_prompt,
            model_id=model_ref.model_id,
            region=model_ref.region,
            timeout_seconds=timeout_seconds,
        )
    raise NotImplementedError(f"Review provider not implemented: {provider}")


async def call_judge_llm(
    client: httpx.AsyncClient,
    *,
    model_ref: ModelRef,
    user_prompt: str,
    timeout_seconds: float,
    system_prompt: str | None = None,
) -> dict:
    provider = model_ref.provider.strip().lower()
    if provider not in SUPPORTED_JUDGE_PROVIDERS:
        raise ServiceUnavailableError(
            message=f"Judge provider is not supported: {provider}",
            error_code="llm_disabled",
        )
    if provider == "anthropic":
        return await anthropic_review.judge_finding(
            client,
            user_prompt=user_prompt,
            model_id=model_ref.model_id,
            timeout_seconds=timeout_seconds,
            system_prompt=system_prompt,
        )
    if provider == "bedrock":
        return await bedrock_review.judge_finding(
            user_prompt=user_prompt,
            model_id=model_ref.model_id,
            region=model_ref.region,
            timeout_seconds=timeout_seconds,
            system_prompt=system_prompt,
        )
    raise ServiceUnavailableError(
        message=f"Judge provider is not supported: {provider}",
        error_code="llm_disabled",
    )
