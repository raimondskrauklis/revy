# backend/scripts/test_anthropic_judge_gateway.py
"""Smoke-test Anthropic judge: optional gateway first, direct API fallback."""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import httpx

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.integrations.anthropic_review import (
    JUDGE_SYSTEM_PROMPT,
    _judge_profiles,
    _post_anthropic_messages,
    _post_structured_judge_smoke,
    _post_with_profile_fallback,
    judge_finding,
    parse_judge_outcome,
)

DEFAULT_PROMPT = (
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

_PARSE_ERRORS = (httpx.HTTPError, ValueError, json.JSONDecodeError, OSError, ServiceUnavailableError)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Anthropic judge gateway smoke test")
    parser.add_argument(
        "--structured",
        action="store_true",
        help="Use output_config json_schema for judge outcome",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Load user prompt from file (e.g. staging manifest export)",
    )
    parser.add_argument(
        "--chars",
        type=int,
        help="Pad or truncate prompt to this character length",
    )
    parser.add_argument(
        "--print-raw",
        action="store_true",
        help="Print raw response text before JSON parse",
    )
    parser.add_argument(
        "--compare-direct",
        action="store_true",
        help="Run each configured profile separately and print parse results",
    )
    return parser.parse_args()


def _load_prompt(args: argparse.Namespace) -> str:
    prompt = args.prompt_file.read_text(encoding="utf-8") if args.prompt_file else DEFAULT_PROMPT
    if args.chars is not None:
        if len(prompt) > args.chars:
            prompt = prompt[: args.chars]
        elif len(prompt) < args.chars:
            prompt = prompt + (" " * (args.chars - len(prompt)))
    return prompt


def _print_config() -> None:
    print("Anthropic judge smoke test")
    print(f"  gateway enabled: {settings.anthropic_gateway_enabled}")
    if settings.anthropic_gateway_enabled:
        print(f"  gateway url: {settings.anthropic_gateway_messages_url}")
        print(f"  gateway model: {settings.effective_anthropic_gateway_judge_model}")
    print(f"  direct enabled: {settings.anthropic_direct_enabled}")
    print(f"  direct model: {settings.revy_anthropic_model}")


def _payload_from_text(text: str) -> dict:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("judge_json_not_object")
    return payload


async def _invoke_profile(
    client: httpx.AsyncClient,
    profile: object,
    *,
    prompt: str,
    structured: bool,
    print_raw: bool,
) -> dict:
    timeout = float(settings.revy_revision_timeout_standard_seconds)
    if structured:
        text = await _post_structured_judge_smoke(
            client,
            profile,
            user_prompt=prompt,
            system_prompt=JUDGE_SYSTEM_PROMPT,
            timeout_seconds=timeout,
        )
    else:
        text = await _post_anthropic_messages(
            client,
            profile,
            system=JUDGE_SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=1024,
            timeout_seconds=timeout,
        )
    if print_raw:
        print("Raw response:")
        print(text)
    payload = _payload_from_text(text)
    outcome, notes = parse_judge_outcome(payload)
    return {"outcome": outcome, "notes": notes, "raw_chars": len(text)}


async def _run_compare_direct(
    client: httpx.AsyncClient,
    *,
    prompt: str,
    structured: bool,
    print_raw: bool,
) -> int:
    profiles = _judge_profiles(None)
    if not profiles:
        print("No judge profiles configured")
        return 1
    print(f"Prompt length: {len(prompt)} chars")
    successes = 0
    for profile in profiles:
        print(f"\n--- profile: {profile.label} ({profile.model_id}) ---")
        try:
            result = await _invoke_profile(
                client,
                profile,
                prompt=prompt,
                structured=structured,
                print_raw=print_raw,
            )
            print(json.dumps(result, indent=2))
            successes += 1
        except _PARSE_ERRORS as exc:
            print(f"FAILED: {exc}")
    return 0 if successes else 1


async def _fetch_payload(
    client: httpx.AsyncClient,
    *,
    prompt: str,
    structured: bool,
    print_raw: bool,
) -> dict:
    timeout = float(settings.revy_revision_timeout_standard_seconds)
    profiles = _judge_profiles(None)
    if not profiles:
        raise ServiceUnavailableError(
            message="No judge profiles configured",
            error_code="llm_disabled",
        )

    if not structured and not print_raw:
        return await judge_finding(client, user_prompt=prompt)

    if structured:
        text = await _post_structured_judge_smoke(
            client,
            profiles[0],
            user_prompt=prompt,
            timeout_seconds=timeout,
        )
    else:
        text = await _post_with_profile_fallback(
            client,
            profiles,
            system=JUDGE_SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=1024,
            timeout_seconds=timeout,
        )

    if print_raw:
        print("Raw response:")
        print(text)
    return _payload_from_text(text)


async def _run() -> int:
    args = _parse_args()
    _print_config()

    if not settings.judge_llm_enabled():
        print(
            "Judge LLM not configured — set ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL "
            "or ANTHROPIC_API_KEY"
        )
        return 1

    prompt = _load_prompt(args)
    print(f"Prompt length: {len(prompt)} chars")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            if args.compare_direct:
                return await _run_compare_direct(
                    client,
                    prompt=prompt,
                    structured=args.structured,
                    print_raw=args.print_raw,
                )

            payload = await _fetch_payload(
                client,
                prompt=prompt,
                structured=args.structured,
                print_raw=args.print_raw,
            )
    except _PARSE_ERRORS as exc:
        print(f"FAILED: {exc}")
        return 1

    print("Response:")
    print(json.dumps(payload, indent=2))
    try:
        outcome, _ = parse_judge_outcome(payload)
    except ValueError as exc:
        print(f"FAILED: {exc}")
        return 1
    print(f"Parsed outcome: {outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
