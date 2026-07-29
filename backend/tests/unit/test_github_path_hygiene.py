# backend/tests/unit/test_github_path_hygiene.py
"""HEAD path hygiene — wave C CS-Q7."""
import uuid
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


@pytest.mark.asyncio
async def test_paths_absent_at_head_malformed_full_name_fail_closed():
    from app.constants.enums import GitHubAccountType, GitHubInstallationStatus
    from app.models.github_installation import GitHubInstallationORM
    from app.models.github_pull_request import GitHubPullRequestORM
    from app.models.github_repository import GitHubRepositoryORM
    from app.services.github_path_hygiene import paths_absent_at_head

    workspace_id = uuid.uuid4()
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state="open",
        head_sha="sha",
        head_ref="main",
        base_ref="main",
        revision_count=1,
    )
    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=99,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
        status=GitHubInstallationStatus.active,
    )
    repository = GitHubRepositoryORM(
        installation_id=pull_request.installation_id,
        workspace_id=workspace_id,
        github_repository_id=1,
        name="invalid",
        full_name="invalid-no-slash",
    )

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[repository, installation])

    result = await paths_absent_at_head(
        session,
        pull_request=pull_request,
        head_sha="sha",
        file_paths=frozenset({"app/a.py"}),
    )
    assert result == {"app/a.py": None}


@pytest.mark.asyncio
async def test_paths_absent_at_head_compare_deleted_fast_path_skips_api():
    from app.constants.enums import GitHubAccountType, GitHubInstallationStatus
    from app.models.github_installation import GitHubInstallationORM
    from app.models.github_pull_request import GitHubPullRequestORM
    from app.models.github_repository import GitHubRepositoryORM
    from app.services.github_path_hygiene import paths_absent_at_head

    workspace_id = uuid.uuid4()
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state="open",
        head_sha="sha",
        head_ref="main",
        base_ref="main",
        revision_count=1,
    )
    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=99,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
        status=GitHubInstallationStatus.active,
    )
    repository = GitHubRepositoryORM(
        installation_id=pull_request.installation_id,
        workspace_id=workspace_id,
        github_repository_id=1,
        name="demo",
        full_name="acme/demo",
    )

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[repository, installation])

    with patch(
        "app.services.github_path_hygiene.path_absent_at_head",
        AsyncMock(return_value=False),
    ) as head_check:
        result = await paths_absent_at_head(
            session,
            pull_request=pull_request,
            head_sha="sha",
            file_paths=frozenset({"gone.py", "app/a.py"}),
            deleted_paths=frozenset({"gone.py"}),
            renamed_from_paths=frozenset(),
        )

    assert result == {"app/a.py": False, "gone.py": True}
    head_check.assert_awaited_once()
