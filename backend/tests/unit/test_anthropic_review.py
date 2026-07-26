# backend/tests/unit/test_anthropic_review.py
"""Anthropic review client — R4 scaffold."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.exceptions import ServiceUnavailableError
from app.integrations.anthropic_review import complete_review, parse_review_json


@pytest.mark.asyncio
async def test_complete_review_disabled_raises():
    client = AsyncMock(spec=httpx.AsyncClient)
    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.anthropic_api_key = None
        with pytest.raises(ServiceUnavailableError) as exc:
            await complete_review(client, user_prompt="review this")
    assert exc.value.error_code == "llm_disabled"


@pytest.mark.asyncio
async def test_complete_review_returns_content():
    payload = {"content": [{"text": json.dumps({"findings": []})}]}
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = payload
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.revy_anthropic_model = "claude-sonnet-4-20250514"
        content = await complete_review(client, user_prompt="review")

    assert json.loads(content)["findings"] == []


def test_parse_review_json_empty_findings():
    assert parse_review_json(json.dumps({"findings": []})) == []
