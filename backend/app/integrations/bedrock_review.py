# backend/app/integrations/bedrock_review.py
"""AWS Bedrock Converse client — MODEL_POLICY M1."""
from __future__ import annotations

import asyncio
import json
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.integrations.anthropic_review import JUDGE_SYSTEM_PROMPT, REVIEW_SYSTEM_PROMPT


def _require_bedrock_configured(*, model_id: str, region: str | None) -> None:
    if not settings.bedrock_enabled():
        raise ServiceUnavailableError(
            message="Bedrock is not configured",
            error_code="llm_disabled",
        )
    if not model_id or not model_id.strip():
        raise ServiceUnavailableError(
            message="Bedrock model is not configured",
            error_code="llm_disabled",
        )
    if not region or not region.strip():
        raise ServiceUnavailableError(
            message="AWS region is not configured",
            error_code="llm_disabled",
        )


def _extract_text(response: dict[str, Any]) -> str:
    output = response.get("output")
    if not isinstance(output, dict):
        raise ServiceUnavailableError(
            message="Bedrock response invalid",
            error_code="llm_error",
        )
    message = output.get("message")
    if not isinstance(message, dict):
        raise ServiceUnavailableError(
            message="Bedrock response invalid",
            error_code="llm_error",
        )
    content = message.get("content")
    if not isinstance(content, list) or not content:
        raise ServiceUnavailableError(
            message="Bedrock response invalid",
            error_code="llm_error",
        )
    first = content[0]
    if not isinstance(first, dict):
        raise ServiceUnavailableError(
            message="Bedrock response invalid",
            error_code="llm_error",
        )
    text = first.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ServiceUnavailableError(
            message="Bedrock response invalid",
            error_code="llm_error",
        )
    return text


def _converse_sync(
    *,
    model_id: str,
    region: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> dict[str, Any]:
    client = boto3.client("bedrock-runtime", region_name=region)
    return client.converse(
        modelId=model_id,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.2},
    )


async def complete_review(
    *,
    user_prompt: str,
    model_id: str,
    region: str | None,
    timeout_seconds: float | None = None,
) -> str:
    _require_bedrock_configured(model_id=model_id, region=region)
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                _converse_sync,
                model_id=model_id,
                region=region,
                system_prompt=REVIEW_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=4096,
            ),
            timeout=timeout_seconds or settings.revy_revision_timeout_standard_seconds,
        )
    except (asyncio.TimeoutError, ClientError, BotoCoreError) as exc:  # noqa: UP041
        raise ServiceUnavailableError(
            message="Bedrock review request failed",
            error_code="llm_error",
        ) from exc
    return _extract_text(response)


async def judge_finding(
    *,
    user_prompt: str,
    model_id: str,
    region: str | None,
    timeout_seconds: float | None = None,
    system_prompt: str | None = None,
) -> dict:
    _require_bedrock_configured(model_id=model_id, region=region)
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                _converse_sync,
                model_id=model_id,
                region=region,
                system_prompt=system_prompt or JUDGE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=1024,
            ),
            timeout=timeout_seconds or settings.revy_revision_timeout_standard_seconds,
        )
    except (asyncio.TimeoutError, ClientError, BotoCoreError) as exc:  # noqa: UP041
        raise ServiceUnavailableError(
            message="Bedrock judge request failed",
            error_code="llm_error",
        ) from exc
    text = _extract_text(response)
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("judge_json_not_object")
    return payload
