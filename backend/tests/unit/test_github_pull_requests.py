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
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM
from app.services.github_pull_requests import (
    _append_revision,
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
            "body": "Fixes login bug",
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
async def test_apply_pull_request_opened_persists_body():
    installation = _installation()
    repository = _repository(installation)
    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[installation, repository, None])
    added: list[object] = []
    session.add = MagicMock(side_effect=lambda obj: added.append(obj))
    session.flush = AsyncMock()

    await apply_pull_request_webhook_event(session, _pull_request_payload(action="opened"))

    pull_requests = [obj for obj in added if isinstance(obj, GitHubPullRequestORM)]
    assert len(pull_requests) == 1
    assert pull_requests[0].body == "Fixes login bug"


@pytest.mark.asyncio
async def test_apply_pull_request_edited_updates_body():
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
        body="Old body",
        revision_count=1,
    )
    existing.id = uuid.uuid4()

    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[installation, repository, existing])
    session.flush = AsyncMock()

    payload = _pull_request_payload(action="edited")
    payload["pull_request"]["body"] = "Updated description"

    await apply_pull_request_webhook_event(session, payload)

    assert existing.body == "Updated description"


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

    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[installation, repository, existing, None, None])

    async def _session_get(_model, revision_id):
        revision = GitHubPullRequestRevisionORM(
            pull_request_id=existing.id,
            revision_number=2,
            head_sha="newsha",
            base_sha="base000",
        )
        revision.id = revision_id
        return revision

    session.get = AsyncMock(side_effect=_session_get)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch(
        "app.services.github_pull_requests.supersede_stale_generations_for_new_revision",
        AsyncMock(),
    ) as supersede_stale_mock:
        with patch(
            "app.services.github_pull_requests.supersede_active_generations_for_revision",
            AsyncMock(),
        ) as supersede_active_mock:
            result = await apply_pull_request_webhook_event(
                session,
                _pull_request_payload(action="synchronize", head_sha="newsha"),
            )

    assert result is not None
    supersede_stale_mock.assert_awaited_once()
    supersede_active_mock.assert_awaited_once()

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
    session.scalar = AsyncMock(side_effect=[installation, repository, existing, None, None])

    async def _session_get(_model, revision_id):
        revision = GitHubPullRequestRevisionORM(
            pull_request_id=existing.id,
            revision_number=2,
            head_sha="newsha",
            base_sha="base000",
        )
        revision.id = revision_id
        return revision

    session.get = AsyncMock(side_effect=_session_get)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch(
        "app.services.github_pull_requests.supersede_stale_generations_for_new_revision",
        AsyncMock(),
    ):
        with patch(
            "app.services.github_pull_requests.supersede_active_generations_for_revision",
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
    existing_revision = GitHubPullRequestRevisionORM(
        pull_request_id=existing.id,
        revision_number=1,
        head_sha="same-sha",
        base_sha="base000",
    )
    existing_revision.id = uuid.uuid4()

    session = AsyncMock()
    session.scalar = AsyncMock(
        side_effect=[installation, repository, existing, existing_revision],
    )
    session.get = AsyncMock(return_value=existing_revision)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch(
        "app.services.github_pull_requests.supersede_stale_generations_for_new_revision",
        AsyncMock(),
    ):
        with patch(
            "app.services.github_pull_requests.supersede_active_generations_for_revision",
            AsyncMock(),
        ):
            await apply_pull_request_webhook_event(
                session,
                _pull_request_payload(action="synchronize", head_sha="same-sha"),
            )

    assert existing.revision_count == 1
    session.add.assert_not_called()
    session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_apply_pull_request_synchronize_same_sha_heals_missing_revision():
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
        head_sha="orphan-sha",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    existing.id = uuid.uuid4()

    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[installation, repository, existing, None, None])

    async def _session_get(_model, revision_id):
        revision = GitHubPullRequestRevisionORM(
            pull_request_id=existing.id,
            revision_number=2,
            head_sha="orphan-sha",
            base_sha="base000",
        )
        revision.id = revision_id
        return revision

    session.get = AsyncMock(side_effect=_session_get)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch(
        "app.services.github_pull_requests.supersede_stale_generations_for_new_revision",
        AsyncMock(),
    ) as supersede_stale_mock:
        with patch(
            "app.services.github_pull_requests.supersede_active_generations_for_revision",
            AsyncMock(),
        ) as supersede_active_mock:
            result = await apply_pull_request_webhook_event(
                session,
                _pull_request_payload(action="synchronize", head_sha="orphan-sha"),
            )

    assert result is not None
    assert existing.revision_count == 2
    session.add.assert_called_once()
    supersede_stale_mock.assert_awaited_once()
    supersede_active_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_issue_comment_heals_orphan_head_revision():
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
        head_sha="orphan-sha",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    pull_request.id = uuid.uuid4()

    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[installation, repository, pull_request, None, None])
    session.add = MagicMock()
    session.flush = AsyncMock()

    result = await apply_issue_comment_webhook_event(session, _issue_comment_payload())

    assert result is not None
    assert result.workspace_id == repository.workspace_id
    session.add.assert_called_once()


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


@pytest.mark.asyncio
async def test_synchronize_returns_existing_revision_when_head_sha_row_exists():
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
        revision_count=2,
    )
    existing.id = uuid.uuid4()
    prior_revision = GitHubPullRequestRevisionORM(
        pull_request_id=existing.id,
        revision_number=2,
        head_sha="retry-sha",
        base_sha="base000",
    )
    prior_revision.id = uuid.uuid4()

    session = _session_with_nested()
    session.scalar = AsyncMock(
        side_effect=[installation, repository, existing, prior_revision],
    )
    session.get = AsyncMock(return_value=prior_revision)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch(
        "app.services.github_pull_requests.supersede_stale_generations_for_new_revision",
        AsyncMock(),
    ) as supersede_stale_mock:
        with patch(
            "app.services.github_pull_requests.supersede_active_generations_for_revision",
            AsyncMock(),
        ) as supersede_active_mock:
            result = await apply_pull_request_webhook_event(
                session,
                _pull_request_payload(action="synchronize", head_sha="retry-sha"),
            )

    assert result is not None
    assert result.revision_id == prior_revision.id
    assert existing.revision_count == 2
    session.add.assert_not_called()
    supersede_stale_mock.assert_awaited_once()
    supersede_active_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_append_revision_pre_check_dedupe_flushes_head_sha():
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=_PR_GITHUB_ID,
        number=7,
        title="Add feature",
        state=GitHubPullRequestState.open,
        head_sha="oldsha",
        head_ref="feature",
        base_ref="main",
        revision_count=2,
    )
    pull_request.id = uuid.uuid4()
    existing = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request.id,
        revision_number=2,
        head_sha="dedupe-sha",
        base_sha="base000",
    )
    existing.id = uuid.uuid4()

    session = _session_with_nested()
    session.scalar = AsyncMock(return_value=existing)
    session.flush = AsyncMock()

    revision = await _append_revision(
        session,
        pull_request=pull_request,
        head_sha="dedupe-sha",
        base_sha="base000",
    )

    assert revision.id == existing.id
    assert pull_request.head_sha == "dedupe-sha"
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_append_revision_recovers_same_head_sha_after_unique_violation():
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=_PR_GITHUB_ID,
        number=7,
        title="Add feature",
        state=GitHubPullRequestState.open,
        head_sha="oldsha",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    pull_request.id = uuid.uuid4()
    raced_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request.id,
        revision_number=2,
        head_sha="newsha",
        base_sha="base000",
    )
    raced_revision.id = uuid.uuid4()

    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[None, raced_revision])
    session.add = MagicMock()
    session.flush = AsyncMock(
        side_effect=[IntegrityError("insert", {}, _UniqueViolation("unique")), None],
    )
    session.refresh = AsyncMock()

    revision = await _append_revision(
        session,
        pull_request=pull_request,
        head_sha="newsha",
        base_sha="base000",
    )

    assert revision.id == raced_revision.id
    assert pull_request.head_sha == "newsha"
    assert session.flush.await_count == 2
    assert session.refresh.await_count == 2


@pytest.mark.asyncio
async def test_append_revision_expunges_failed_revision_before_retry():
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=_PR_GITHUB_ID,
        number=7,
        title="Add feature",
        state=GitHubPullRequestState.open,
        head_sha="sha-a",
        head_ref="feature",
        base_ref="main",
        revision_count=12,
    )
    pull_request.id = uuid.uuid4()

    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[None, None])
    session.flush = AsyncMock(
        side_effect=[IntegrityError("insert", {}, _UniqueViolation("unique")), None],
    )

    async def _refresh_stub(pr: GitHubPullRequestORM) -> None:
        pr.revision_count = 13

    session.refresh = AsyncMock(side_effect=_refresh_stub)
    session.expunge = MagicMock()

    await _append_revision(
        session,
        pull_request=pull_request,
        head_sha="sha-b",
        base_sha="base000",
    )

    session.expunge.assert_called_once()
    session.refresh.assert_awaited()


@pytest.mark.asyncio
async def test_append_revision_retries_next_revision_number_after_different_sha_collision():
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=_PR_GITHUB_ID,
        number=7,
        title="Add feature",
        state=GitHubPullRequestState.open,
        head_sha="sha-a",
        head_ref="feature",
        base_ref="main",
        revision_count=12,
    )
    pull_request.id = uuid.uuid4()

    session = _session_with_nested()
    session.scalar = AsyncMock(side_effect=[None, None])
    session.add = MagicMock()
    session.flush = AsyncMock(
        side_effect=[IntegrityError("insert", {}, _UniqueViolation("unique")), None],
    )

    async def _refresh_stub(pr: GitHubPullRequestORM) -> None:
        pr.revision_count = 13

    session.refresh = AsyncMock(side_effect=_refresh_stub)

    revision = await _append_revision(
        session,
        pull_request=pull_request,
        head_sha="sha-b",
        base_sha="base000",
    )

    assert revision.revision_number == 14
    assert revision.head_sha == "sha-b"
    assert pull_request.revision_count == 14
    assert pull_request.head_sha == "sha-b"
