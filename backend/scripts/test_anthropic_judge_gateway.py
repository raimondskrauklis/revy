# backend/scripts/test_anthropic_judge_gateway.py
"""Smoke-test Anthropic judge: optional gateway first, direct API fallback."""
from __future__ import annotations

import asyncio
import json

import httpx

from app.core.config import settings
from app.integrations.anthropic_review import judge_finding


async def _run() -> int:
    print("Anthropic judge smoke test")
    print(f"  gateway enabled: {settings.anthropic_gateway_enabled}")
    if settings.anthropic_gateway_enabled:
        print(f"  gateway url: {settings.anthropic_gateway_messages_url}")
        print(f"  gateway model: {settings.effective_anthropic_gateway_judge_model}")
    print(f"  direct enabled: {settings.anthropic_direct_enabled}")
    print(f"  direct model: {settings.revy_anthropic_model}")

    if not settings.judge_llm_enabled():
        print(
            "Judge LLM not configured — set ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL "
            "or ANTHROPIC_API_KEY"
        )
        return 1

    prompt = (
        "Title: Possible null dereference\n"
        "Severity: error\n"
        "Category: bug\n"
        "File: app/handler.py\n"
        "Line: 42\n"
        "Message: value may be None before access\n"
        "Evidence (code excerpt from diff):\n"
        "if value is None:\n"
        "    raise ValueError('missing')\n"
        "return value.upper()\n"
    )

    async with httpx.AsyncClient(timeout=120.0) as client:
        raw = await judge_finding(client, user_prompt=prompt)
    print("Response:")
    print(json.dumps(raw, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
