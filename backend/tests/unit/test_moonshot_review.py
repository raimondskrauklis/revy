# backend/tests/unit/test_moonshot_review.py
"""Moonshot review client — R4."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.exceptions import ServiceUnavailableError
from app.integrations.moonshot_review import complete_review, parse_review_json


@pytest.mark.asyncio
async def test_complete_review_disabled_raises():
    client = AsyncMock(spec=httpx.AsyncClient)
    with patch("app.integrations.moonshot_review.settings") as mock_settings:
        mock_settings.llm_enabled = False
        with pytest.raises(ServiceUnavailableError) as exc:
            await complete_review(client, profile="standard", user_prompt="review this")
    assert exc.value.error_code == "llm_disabled"


@pytest.mark.asyncio
async def test_complete_review_returns_content():
    payload = {
        "choices": [{"message": {"content": json.dumps({"findings": []})}}],
    }
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = payload
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.moonshot_review.settings") as mock_settings:
        mock_settings.llm_enabled = True
        mock_settings.moonshot_api_key = "test-key"
        mock_settings.revy_moonshot_model_for_profile.return_value = "kimi-k2.7-code"
        content = await complete_review(client, profile="standard", user_prompt="review")

    assert json.loads(content)["findings"] == []


def test_parse_review_json_valid():
    raw = json.dumps(
        {
            "findings": [
                {
                    "severity": "warning",
                    "category": "bug",
                    "title": "Null check",
                    "message": "Possible null dereference",
                }
            ]
        }
    )
    findings = parse_review_json(raw)
    assert len(findings) == 1
    assert findings[0]["title"] == "Null check"


def test_parse_review_json_invalid_raises():
    with pytest.raises(ValueError):
        parse_review_json(json.dumps([]))
