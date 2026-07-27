# backend/tests/unit/test_github_pull_requests.py
"""GitHub pull request service — R2 PR ingestion."""
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.constants.enums import (
    GitHubAccountType,
    GitHubInstallationStatus,
    GitHubPullRequestState,
    GitHubRepositoryStatus,
)
from app.core.pagination import CursorParams
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pull_request import GitHubPullRequestORM
from app.models.github_repository import GitHubRepositoryORM
from app.services.github_pull_requests import (
    apply_issue_comment_webhook_event,
    apply_pull_request_review_webhook_event,
    apply_pull_request_webhook_event,
    list_github_pull_requests,
)

_INSTALLATION_ID = 42
_REPO_GITHUB_ID = 100
_PR_GITHUB_ID = 5001


class _UniqueViolation(Exception):
    pgcode = "23505"


def _session_with_nested() -> AsyncMock:
    session = AsyncMock()

    @asynccontextmanager
    async def _begin_nested():
        yield

    session.begin_nested = MagicMock(side_effect=_begin_nested)
    return session


def _installation() -> GitHubInstallationORM:
    row = GitHubInstallationORM(
        workspace_id=uuid.uuid4(),
        github_installation_id=_INSTALLATION_ID,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
        status=GitHubInstallationStatus.active,
    )
    row.id = uuid.uuid4()
    return row


def _repository(installation: GitHubInstallationORM) -> GitHubRepositoryORM:
    row = GitHubRepositoryORM(
        installation_id=installation.id,
        workspace_id=installation.workspace_id,
        github_repository_id=_REPO_GITHUB_ID,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )
    row.id = uuid.uuid4()
    return row


def _pull_request_payload(*, action: str, head_sha: str = "abc123", draft: bool = False) -> dict:
    return {
        "action": action,
        "installation": {"id": _INSTALLATION_ID},
        "repository": {"id": _REPO_GITHUB_ID},
        "pull_request": {
            "id": _PR_GITHUB_ID,
            "number": 7,
            "title": "Add feature",
            "state": "open",
            "draft": draft,
            "html_url": "https://github.com/acme/demo/pull/7",
            "head": {"sha": head_sha, "ref": "feature"},
            "base": {"sha": "base000", "ref": "main"},
        },
    }


@pytest.mark.asyncio
async def test_apply_pull_request_opened_creates_pr_and_revision():
    installation = _installation()
    repository = _repository(installation)
    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[installation, repository, None])
    session.add = MagicMock()
    session.flush = AsyncMock()

    await apply_pull_request_webhook_event(session, _pull_request_payload(action="opened"))

    assert session.add.call_count == 2


@pytest.mark.asyncio
async def test_apply_pull_request_opened_persists_base_sha():
    installation = _installation()
    repository = _repository(installation)
    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[installation, repository, None])
    added: list[object] = []
    session.add = MagicMock(side_effect=lambda obj: added.append(obj))
    session.flush = AsyncMock()

    await apply_pull_request_webhook_event(session, _pull_request_payload(action="opened"))

    revisions = [obj for obj in added if hasattr(obj, "base_sha")]
    assert len(revisions) == 1
    assert revisions[0].base_sha == "base000"


@pytest.mark.asyncio
async def test_apply_pull_request_opened_handles_concurrent_insert():
    installation = _installation()
    repository = _repository(installation)
    raced = GitHubPullRequestORM(
        repository_id=repository.id,
        workspace_id=repository.workspace_id,
        installation_id=repository.installation_id,
        github_pull_request_id=_PR_GITHUB_ID,
        number=7,
        title="Old title",
        state=GitHubPullRequestState.open,
        head_sha="oldsha",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    raced.id = uuid.uuid4()

    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[installation, repository, None, raced])
    session.add = MagicMock()
    session.flush = AsyncMock(
        side_effect=[IntegrityError("insert", {}, _UniqueViolation("unique")), None],
    )

    await apply_pull_request_webhook_event(session, _pull_request_payload(action="opened"))

    session.rollback.assert_not_called()
    assert session.flush.await_count == 2
    assert raced.title == "Add feature"
    assert raced.head_sha == "abc123"


@pytest.mark.asyncio
async def test_apply_pull_request_synchronize_appends_revision():
    installation = _installation()
    repository = _repository(installation)
    existing = GitHubPullRequestORM(
        repository_id=repository.id,
        workspace_id=repository.workspace_id,
        installation_id=repository.installation_id,
        github_pull_request_id=_PR_GITHUB_ID,
        number=7,
        title="Add feature",
        state=GitHubPullRequestState.open,
        head_sha="oldsha",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    existing.id = uuid.uuid4()

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[installation, repository, existing])
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch(
        "app.services.github_pull_requests.apply_resolution_status_for_synchronize",
        AsyncMock(return_value=0),
    ):
        with patch(
            "app.services.github_pull_requests.supersede_stale_generations_for_new_revision",
            AsyncMock(),
        ) as supersede_mock:
            await apply_pull_request_webhook_event(
                session,
                _pull_request_payload(action="synchronize", head_sha="newsha"),
            )

    supersede_mock.assert_awaited_once()

    assert existing.revision_count == 2
    assert existing.head_sha == "newsha"
    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_apply_pull_request_synchronize_updates_is_draft():
    installation = _installation()
    repository = _repository(installation)
    existing = GitHubPullRequestORM(
        repository_id=repository.id,
        workspace_id=repository.workspace_id,
        installation_id=repository.installation_id,
        github_pull_request_id=_PR_GITHUB_ID,
        number=7,
        title="Add feature",
        state=GitHubPullRequestState.open,
        head_sha="oldsha",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
        is_draft=False,
    )
    existing.id = uuid.uuid4()

    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[installation, repository, existing])
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch(
        "app.services.github_pull_requests.apply_resolution_status_for_synchronize",
        AsyncMock(return_value=0),
    ):
        with patch(
            "app.services.github_pull_requests.supersede_stale_generations_for_new_revision",
            AsyncMock(),
        ):
            await apply_pull_request_webhook_event(
                session,
                _pull_request_payload(action="synchronize", head_sha="newsha", draft=True),
            )

    assert existing.is_draft is True
    assert existing.revision_count == 2


@pytest.mark.asyncio
async def test_apply_pull_request_synchronize_same_sha_skips_revision():
    installation = _installation()
    repository = _repository(installation)
    existing = GitHubPullRequestORM(
        repository_id=repository.id,
        workspace_id=repository.workspace_id,
        installation_id=repository.installation_id,
        github_pull_request_id=_PR_GITHUB_ID,
        number=7,
        title="Add feature",
        state=GitHubPullRequestState.open,
        head_sha="same-sha",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    existing.id = uuid.uuid4()

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[installation, repository, existing])
    session.add = MagicMock()
    session.flush = AsyncMock()

    await apply_pull_request_webhook_event(
        session,
        _pull_request_payload(action="synchronize", head_sha="same-sha"),
    )

    assert existing.revision_count == 1
    session.add.assert_not_called()
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_pull_request_orphan_repository_no_op():
    installation = _installation()
    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[installation, None])

    await apply_pull_request_webhook_event(session, _pull_request_payload(action="opened"))

    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_apply_pull_request_review_stores_review():
    installation = _installation()
    repository = _repository(installation)
    pull_request = GitHubPullRequestORM(
        repository_id=repository.id,
        workspace_id=repository.workspace_id,
        installation_id=repository.installation_id,
        github_pull_request_id=_PR_GITHUB_ID,
        number=7,
        title="Add feature",
        state=GitHubPullRequestState.open,
        head_sha="abc123",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    pull_request.id = uuid.uuid4()

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[installation, repository, pull_request, None])
    session.add = MagicMock()
    session.flush = AsyncMock()

    await apply_pull_request_review_webhook_event(
        session,
        {
            "action": "submitted",
            "installation": {"id": _INSTALLATION_ID},
            "repository": {"id": _REPO_GITHUB_ID},
            "pull_request": _pull_request_payload(action="opened")["pull_request"],
            "review": {
                "id": 9001,
                "user": {"login": "reviewer"},
                "state": "approved",
                "submitted_at": "2026-07-26T10:00:00Z",
            },
        },
    )

    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_list_github_pull_requests_returns_cursor_page():
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    repository = GitHubRepositoryORM(
        installation_id=uuid.uuid4(),
        workspace_id=workspace_id,
        github_repository_id=1,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )
    repository.id = repository_id

    row = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha="sha",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    row.id = uuid.uuid4()
    row.created_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=repository)
    session.scalars = AsyncMock(return_value=[row])

    page = await list_github_pull_requests(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        params=CursorParams(limit=50),
    )

    assert len(page.items) == 1
    assert page.items[0].title == "PR"


def _issue_comment_payload(*, body: str = "@revy review") -> dict:
    return {
        "action": "created",
        "installation": {"id": _INSTALLATION_ID},
        "repository": {"id": _REPO_GITHUB_ID},
        "issue": {
            "number": 7,
            "state": "open",
            "pull_request": {"url": "https://api.github.com/repos/acme/demo/pulls/7"},
        },
        "comment": {
            "body": body,
            "user": {"login": "human"},
        },
    }


@pytest.mark.asyncio
async def test_apply_issue_comment_skips_draft_pull_request():
    installation = _installation()
    repository = _repository(installation)
    pull_request = GitHubPullRequestORM(
        repository_id=repository.id,
        workspace_id=repository.workspace_id,
        installation_id=repository.installation_id,
        github_pull_request_id=_PR_GITHUB_ID,
        number=7,
        title="Draft PR",
        state=GitHubPullRequestState.open,
        head_sha="draftsha",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
        is_draft=True,
    )
    pull_request.id = uuid.uuid4()

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[installation, repository, pull_request])

    result = await apply_issue_comment_webhook_event(session, _issue_comment_payload())

    assert result is None


@pytest.mark.asyncio
async def test_apply_pull_request_converted_to_draft_updates_flag():
    installation = _installation()
    repository = _repository(installation)
    existing = GitHubPullRequestORM(
        repository_id=repository.id,
        workspace_id=repository.workspace_id,
        installation_id=repository.installation_id,
        github_pull_request_id=_PR_GITHUB_ID,
        number=7,
        title="Add feature",
        state=GitHubPullRequestState.open,
        head_sha="abc123",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
        is_draft=False,
    )
    existing.id = uuid.uuid4()

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[installation, repository, existing])
    session.flush = AsyncMock()

    payload = _pull_request_payload(action="converted_to_draft")
    payload["pull_request"]["draft"] = True

    result = await apply_pull_request_webhook_event(session, payload)

    assert result is None
    assert existing.is_draft is True
