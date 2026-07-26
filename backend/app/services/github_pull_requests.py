# backend/app/services/github_pull_requests.py
"""GitHub pull request ingestion — R2."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import GitHubPullRequestState, GitHubRepositoryStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.core.pagination import (
    CursorMeta,
    CursorParams,
    CursorResponse,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
)
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pull_request import (
    GitHubPullRequestORM,
    GitHubPullRequestReviewORM,
    GitHubPullRequestRevisionORM,
)
from app.models.github_repository import GitHubRepositoryORM
from app.schemas.github_pull_request import GitHubPullRequestResponse

logger = get_logger(__name__)

_PULL_REQUEST_ACTIONS = frozenset({"opened", "synchronize", "closed", "reopened"})
_REVIEW_ACTIONS = frozenset({"submitted", "edited", "dismissed"})


def _parse_github_datetime(value: str | None) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _extract_pr_fields(pull_request: dict[str, Any]) -> dict[str, Any] | None:
    raw_id = pull_request.get("id")
    number = pull_request.get("number")
    title = pull_request.get("title")
    state = pull_request.get("state")
    head = pull_request.get("head")
    base = pull_request.get("base")
    if (
        not isinstance(raw_id, int)
        or not isinstance(number, int)
        or not isinstance(title, str)
        or not isinstance(state, str)
        or not isinstance(head, dict)
        or not isinstance(base, dict)
    ):
        return None

    head_sha = head.get("sha")
    head_ref = head.get("ref")
    base_ref = base.get("ref")
    if not isinstance(head_sha, str) or not isinstance(head_ref, str) or not isinstance(base_ref, str):
        return None

    try:
        pr_state = GitHubPullRequestState(state)
    except ValueError:
        return None

    html_url = pull_request.get("html_url")
    return {
        "github_pull_request_id": raw_id,
        "number": number,
        "title": title,
        "state": pr_state,
        "head_sha": head_sha,
        "head_ref": head_ref,
        "base_ref": base_ref,
        "html_url": html_url if isinstance(html_url, str) else None,
    }


async def _resolve_repository(
    session: AsyncSession,
    payload: dict[str, Any],
) -> GitHubRepositoryORM | None:
    installation_payload = payload.get("installation")
    repository_payload = payload.get("repository")
    if not isinstance(installation_payload, dict) or not isinstance(repository_payload, dict):
        return None

    github_installation_id = installation_payload.get("id")
    github_repository_id = repository_payload.get("id")
    if not isinstance(github_installation_id, int) or not isinstance(github_repository_id, int):
        return None

    installation = await session.scalar(
        select(GitHubInstallationORM).where(
            GitHubInstallationORM.github_installation_id == github_installation_id,
        )
    )
    if installation is None:
        logger.warning(
            "github_pull_request_orphan_installation",
            extra={"github_installation_id": github_installation_id},
        )
        return None

    repository = await session.scalar(
        select(GitHubRepositoryORM).where(
            GitHubRepositoryORM.installation_id == installation.id,
            GitHubRepositoryORM.github_repository_id == github_repository_id,
            GitHubRepositoryORM.status == GitHubRepositoryStatus.active,
        )
    )
    if repository is None:
        logger.warning(
            "github_pull_request_orphan_repository",
            extra={
                "github_installation_id": github_installation_id,
                "github_repository_id": github_repository_id,
            },
        )
        return None

    return repository


async def _find_pull_request(
    session: AsyncSession,
    *,
    repository_id: UUID,
    github_pull_request_id: int,
) -> GitHubPullRequestORM | None:
    return await session.scalar(
        select(GitHubPullRequestORM).where(
            GitHubPullRequestORM.repository_id == repository_id,
            GitHubPullRequestORM.github_pull_request_id == github_pull_request_id,
        )
    )


async def _append_revision(
    session: AsyncSession,
    *,
    pull_request: GitHubPullRequestORM,
    head_sha: str,
) -> GitHubPullRequestRevisionORM:
    pull_request.revision_count += 1
    pull_request.head_sha = head_sha
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request.id,
        revision_number=pull_request.revision_count,
        head_sha=head_sha,
    )
    session.add(revision)
    await session.flush()
    return revision


async def _upsert_pull_request(
    session: AsyncSession,
    *,
    repository: GitHubRepositoryORM,
    fields: dict[str, Any],
    create_revision: bool,
) -> GitHubPullRequestORM:
    existing = await _find_pull_request(
        session,
        repository_id=repository.id,
        github_pull_request_id=fields["github_pull_request_id"],
    )
    if existing is None:
        pull_request = GitHubPullRequestORM(
            repository_id=repository.id,
            workspace_id=repository.workspace_id,
            installation_id=repository.installation_id,
            revision_count=1,
            **fields,
        )
        session.add(pull_request)
        await session.flush()
        session.add(
            GitHubPullRequestRevisionORM(
                pull_request_id=pull_request.id,
                revision_number=1,
                head_sha=fields["head_sha"],
            )
        )
        await session.flush()
        return pull_request

    existing.title = fields["title"]
    existing.state = fields["state"]
    existing.head_ref = fields["head_ref"]
    existing.base_ref = fields["base_ref"]
    existing.html_url = fields["html_url"]
    existing.number = fields["number"]

    if create_revision and fields["head_sha"] != existing.head_sha:
        await _append_revision(session, pull_request=existing, head_sha=fields["head_sha"])
    else:
        existing.head_sha = fields["head_sha"]
        await session.flush()

    return existing


async def apply_pull_request_webhook_event(
    session: AsyncSession,
    payload: dict[str, Any],
) -> None:
    action = payload.get("action")
    if not isinstance(action, str) or action not in _PULL_REQUEST_ACTIONS:
        if isinstance(action, str):
            logger.info("github_pull_request_action_ignored", extra={"action": action})
        return

    pull_request_payload = payload.get("pull_request")
    if not isinstance(pull_request_payload, dict):
        return

    fields = _extract_pr_fields(pull_request_payload)
    if fields is None:
        return

    repository = await _resolve_repository(session, payload)
    if repository is None:
        return

    if action == "opened":
        await _upsert_pull_request(session, repository=repository, fields=fields, create_revision=False)
        return

    if action == "synchronize":
        existing = await _find_pull_request(
            session,
            repository_id=repository.id,
            github_pull_request_id=fields["github_pull_request_id"],
        )
        if existing is None:
            await _upsert_pull_request(session, repository=repository, fields=fields, create_revision=False)
            return
        existing.title = fields["title"]
        existing.state = fields["state"]
        existing.head_ref = fields["head_ref"]
        existing.base_ref = fields["base_ref"]
        existing.html_url = fields["html_url"]
        if fields["head_sha"] == existing.head_sha:
            await session.flush()
            return
        await _append_revision(session, pull_request=existing, head_sha=fields["head_sha"])
        return

    if action in {"closed", "reopened"}:
        existing = await _find_pull_request(
            session,
            repository_id=repository.id,
            github_pull_request_id=fields["github_pull_request_id"],
        )
        if existing is None:
            logger.warning(
                "github_pull_request_state_orphan",
                extra={
                    "action": action,
                    "github_pull_request_id": fields["github_pull_request_id"],
                },
            )
            return
        existing.state = fields["state"]
        existing.title = fields["title"]
        existing.html_url = fields["html_url"]
        await session.flush()


async def apply_pull_request_review_webhook_event(
    session: AsyncSession,
    payload: dict[str, Any],
) -> None:
    action = payload.get("action")
    if not isinstance(action, str) or action not in _REVIEW_ACTIONS:
        if isinstance(action, str):
            logger.info("github_pull_request_review_action_ignored", extra={"action": action})
        return

    review_payload = payload.get("review")
    pull_request_payload = payload.get("pull_request")
    if not isinstance(review_payload, dict) or not isinstance(pull_request_payload, dict):
        return

    fields = _extract_pr_fields(pull_request_payload)
    if fields is None:
        return

    repository = await _resolve_repository(session, payload)
    if repository is None:
        return

    pull_request = await _find_pull_request(
        session,
        repository_id=repository.id,
        github_pull_request_id=fields["github_pull_request_id"],
    )
    if pull_request is None:
        pull_request = await _upsert_pull_request(
            session,
            repository=repository,
            fields=fields,
            create_revision=False,
        )

    raw_review_id = review_payload.get("id")
    user = review_payload.get("user")
    state = review_payload.get("state")
    if not isinstance(raw_review_id, int) or not isinstance(user, dict) or not isinstance(state, str):
        return

    login = user.get("login")
    if not isinstance(login, str):
        return

    submitted_at = _parse_github_datetime(review_payload.get("submitted_at"))
    if submitted_at is None:
        submitted_at = datetime.now(UTC)

    existing_review = await session.scalar(
        select(GitHubPullRequestReviewORM).where(
            GitHubPullRequestReviewORM.github_review_id == raw_review_id,
        )
    )
    if existing_review is None:
        session.add(
            GitHubPullRequestReviewORM(
                pull_request_id=pull_request.id,
                github_review_id=raw_review_id,
                author_login=login,
                state=state,
                submitted_at=submitted_at,
            )
        )
    else:
        existing_review.author_login = login
        existing_review.state = state
        existing_review.submitted_at = submitted_at

    await session.flush()


async def list_github_pull_requests(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    params: CursorParams,
) -> CursorResponse[GitHubPullRequestResponse]:
    repository = await session.scalar(
        select(GitHubRepositoryORM).where(
            GitHubRepositoryORM.id == repository_id,
            GitHubRepositoryORM.workspace_id == workspace_id,
            GitHubRepositoryORM.status == GitHubRepositoryStatus.active,
        )
    )
    if repository is None:
        raise NotFoundError("GitHub repository not found")

    stmt = select(GitHubPullRequestORM).where(
        GitHubPullRequestORM.workspace_id == workspace_id,
        GitHubPullRequestORM.repository_id == repository_id,
    )

    if params.cursor:
        try:
            cursor_ts, cursor_id = decode_cursor(params.cursor)
        except InvalidCursorError as exc:
            raise ValidationError(message="Invalid cursor", field="cursor") from exc
        stmt = stmt.where(
            (GitHubPullRequestORM.created_at < cursor_ts)
            | ((GitHubPullRequestORM.created_at == cursor_ts) & (GitHubPullRequestORM.id < cursor_id))
        )

    stmt = stmt.order_by(
        GitHubPullRequestORM.created_at.desc(),
        GitHubPullRequestORM.id.desc(),
    ).limit(params.limit + 1)
    rows = list(await session.scalars(stmt))

    has_next = len(rows) > params.limit
    if has_next:
        rows = rows[: params.limit]

    next_cursor = None
    if has_next and rows:
        last = rows[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    return CursorResponse(
        items=[GitHubPullRequestResponse.model_validate(row) for row in rows],
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )
