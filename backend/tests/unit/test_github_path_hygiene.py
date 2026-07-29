# backend/tests/unit/test_github_path_hygiene.py
"""HEAD path hygiene — wave C CS-Q7."""
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.exceptions import NotFoundError
from app.services.github_path_hygiene import hygiene_path_gone, path_absent_at_head


@pytest.mark.asyncio
async def test_path_absent_at_head_true_on_contents_not_found():
    client = AsyncMock()
    with patch(
        "app.services.github_path_hygiene.fetch_repository_file_at_sha",
        AsyncMock(
            side_effect=NotFoundError(
                message="missing",
                error_code="github_contents_not_found",
            )
        ),
    ):
        result = await path_absent_at_head(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            file_path="gone.py",
            head_sha="abc",
        )
    assert result is True


@pytest.mark.asyncio
async def test_path_absent_at_head_false_when_file_exists():
    client = AsyncMock()
    with patch(
        "app.services.github_path_hygiene.fetch_repository_file_at_sha",
        AsyncMock(return_value="content"),
    ):
        result = await path_absent_at_head(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            file_path="app/a.py",
            head_sha="abc",
        )
    assert result is False


@pytest.mark.asyncio
async def test_path_absent_at_head_none_on_api_error():
    client = AsyncMock()
    with patch(
        "app.services.github_path_hygiene.fetch_repository_file_at_sha",
        AsyncMock(side_effect=httpx.HTTPError("network")),
    ):
        result = await path_absent_at_head(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            file_path="app/a.py",
            head_sha="abc",
        )
    assert result is None


def test_hygiene_path_gone_skips_renamed_from_paths():
    assert hygiene_path_gone(
        "old.py",
        absent_at_head=True,
        renamed_from_paths=frozenset({"old.py"}),
    ) is False


def test_hygiene_path_gone_returns_absent_at_head():
    assert hygiene_path_gone(
        "gone.py",
        absent_at_head=True,
        renamed_from_paths=frozenset(),
    ) is True
    assert hygiene_path_gone(
        "gone.py",
        absent_at_head=None,
        renamed_from_paths=frozenset(),
    ) is None
