# backend/app/services/github_pull_requests.py
"""GitHub pull request ingestion — R2."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import GitHubPullRequestState, GitHubRepositoryStatus
from app.core.config import settings
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
from app.services.github_generation_lifecycle import supersede_stale_generations_for_new_revision
from app.services.github_resolution_metrics import apply_resolution_status_for_synchronize

logger = get_logger(__name__)

_UNIQUE_VIOLATION_PG_CODE = "23505"

_PULL_REQUEST_ACTIONS = frozenset(
    {
        "opened",
        "synchronize",
        "closed",
        "reopened",
        "converted_to_draft",
        "ready_for_review",
        "edited",
    }
)
_REVIEW_ACTIONS = frozenset({"submitted", "edited", "dismissed"})
_REVY_REVIEW_COMMAND = re.compile(r"@revy\s+review\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class PullRequestWebhookResult:
    workspace_id: UUID
    revision_id: UUID
    new_revision: bool
    action: str


@dataclass(frozen=True, slots=True)
class IssueCommentPipelineIntent:
    workspace_id: UUID
    revision_id: UUID


def _is_unique_violation(exc: IntegrityError) -> bool:
    orig = exc.orig
    return orig is not None and getattr(orig, "pgcode", None) == _UNIQUE_VIOLATION_PG_CODE


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
    base_sha = base.get("sha")
    if (
        not isinstance(head_sha, str)
        or not isinstance(head_ref, str)
        or not isinstance(base_ref, str)
        or not isinstance(base_sha, str)
    ):
        return None

    try:
        pr_state = GitHubPullRequestState(state)
    except ValueError:
        return None

    html_url = pull_request.get("html_url")
    body_raw = pull_request.get("body")
    body = body_raw if isinstance(body_raw, str) and body_raw.strip() else None
    return {
        "github_pull_request_id": raw_id,
        "number": number,
        "title": title,
        "state": pr_state,
        "head_sha": head_sha,
        "head_ref": head_ref,
        "base_ref": base_ref,
        "base_sha": base_sha,
        "html_url": html_url if isinstance(html_url, str) else None,
        "body": body,
        "is_draft": pull_request.get("draft") is True,
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
    base_sha: str | None,
) -> GitHubPullRequestRevisionORM:
    existing_revision = await _get_revision_for_head_sha(
        session,
        pull_request_id=pull_request.id,
        head_sha=head_sha,
    )
    if existing_revision is not None:
        logger.info(
            "github_revision_append_deduped",
            extra={
                "pull_request_id": str(pull_request.id),
                "head_sha": head_sha,
                "reason": "same_head_sha",
                "revision_id": str(existing_revision.id),
            },
        )
        pull_request.head_sha = head_sha
        await session.flush()
        return existing_revision

    last_error: IntegrityError | None = None
    for attempt in range(2):
        if attempt == 1:
            await session.refresh(pull_request)
            raced_revision = await _get_revision_for_head_sha(
                session,
                pull_request_id=pull_request.id,
                head_sha=head_sha,
            )
            if raced_revision is not None:
                logger.info(
                    "github_revision_append_deduped",
                    extra={
                        "pull_request_id": str(pull_request.id),
                        "head_sha": head_sha,
                        "reason": "same_head_sha",
                        "revision_id": str(raced_revision.id),
                    },
                )
                pull_request.head_sha = head_sha
                await session.flush()
                return raced_revision

        next_revision_number = pull_request.revision_count + 1
        revision = GitHubPullRequestRevisionORM(
            pull_request_id=pull_request.id,
            revision_number=next_revision_number,
            head_sha=head_sha,
            base_sha=base_sha,
        )
        try:
            async with session.begin_nested():
                session.add(revision)
                pull_request.revision_count = next_revision_number
                pull_request.head_sha = head_sha
                await session.flush()
            return revision
        except IntegrityError as exc:
            if not _is_unique_violation(exc):
                raise
            session.expunge(revision)
            last_error = exc
            logger.info(
                "github_revision_append_deduped",
                extra={
                    "pull_request_id": str(pull_request.id),
                    "head_sha": head_sha,
                    "reason": "revision_number_retry",
                    "attempt": attempt + 1,
                },
            )

    assert last_error is not None
    raise last_error


async def _create_pull_request(
    session: AsyncSession,
    *,
    repository: GitHubRepositoryORM,
    fields: dict[str, Any],
) -> tuple[GitHubPullRequestORM, GitHubPullRequestRevisionORM]:
    base_sha = fields.get("base_sha")
    pr_fields = {key: value for key, value in fields.items() if key != "base_sha"}
    pull_request = GitHubPullRequestORM(
        repository_id=repository.id,
        workspace_id=repository.workspace_id,
        installation_id=repository.installation_id,
        revision_count=1,
        **pr_fields,
    )
    session.add(pull_request)
    await session.flush()
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request.id,
        revision_number=1,
        head_sha=fields["head_sha"],
        base_sha=base_sha if isinstance(base_sha, str) else None,
    )
    session.add(revision)
    await session.flush()
    return pull_request, revision


async def _upsert_pull_request(
    session: AsyncSession,
    *,
    repository: GitHubRepositoryORM,
    fields: dict[str, Any],
    create_revision: bool,
) -> tuple[GitHubPullRequestORM, GitHubPullRequestRevisionORM | None]:
    existing = await _find_pull_request(
        session,
        repository_id=repository.id,
        github_pull_request_id=fields["github_pull_request_id"],
    )
    if existing is None:
        try:
            async with session.begin_nested():
                return await _create_pull_request(session, repository=repository, fields=fields)
        except IntegrityError as exc:
            if not _is_unique_violation(exc):
                raise
            existing = await _find_pull_request(
                session,
                repository_id=repository.id,
                github_pull_request_id=fields["github_pull_request_id"],
            )
            if existing is None:
                raise

    existing.title = fields["title"]
    existing.state = fields["state"]
    existing.head_ref = fields["head_ref"]
    existing.base_ref = fields["base_ref"]
    existing.html_url = fields["html_url"]
    existing.number = fields["number"]
    existing.is_draft = fields["is_draft"]
    existing.body = fields.get("body")

    if create_revision and fields["head_sha"] != existing.head_sha:
        existing_revision = await _get_revision_for_head_sha(
            session,
            pull_request_id=existing.id,
            head_sha=fields["head_sha"],
        )
        if existing_revision is not None:
            existing.head_sha = fields["head_sha"]
            await session.flush()
            return existing, existing_revision
        revision = await _append_revision(
            session,
            pull_request=existing,
            head_sha=fields["head_sha"],
            base_sha=fields.get("base_sha"),
        )
        return existing, revision

    existing.head_sha = fields["head_sha"]
    await session.flush()
    return existing, None


async def _get_revision_for_head_sha(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    head_sha: str,
) -> GitHubPullRequestRevisionORM | None:
    return await session.scalar(
        select(GitHubPullRequestRevisionORM)
        .where(
            GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            GitHubPullRequestRevisionORM.head_sha == head_sha,
        )
        .order_by(GitHubPullRequestRevisionORM.revision_number.desc())
        .limit(1)
    )


async def apply_pull_request_webhook_event(
    session: AsyncSession,
    payload: dict[str, Any],
) -> PullRequestWebhookResult | None:
    action = payload.get("action")
    if not isinstance(action, str) or action not in _PULL_REQUEST_ACTIONS:
        if isinstance(action, str):
            logger.info("github_pull_request_action_ignored", extra={"action": action})
        return None

    pull_request_payload = payload.get("pull_request")
    if not isinstance(pull_request_payload, dict):
        return None

    fields = _extract_pr_fields(pull_request_payload)
    if fields is None:
        return None

    repository = await _resolve_repository(session, payload)
    if repository is None:
        return None

    if action == "opened":
        _pull_request, new_revision = await _upsert_pull_request(
            session,
            repository=repository,
            fields=fields,
            create_revision=False,
        )
        if new_revision is None:
            return None
        return PullRequestWebhookResult(
            workspace_id=repository.workspace_id,
            revision_id=new_revision.id,
            new_revision=True,
            action=action,
        )

    if action == "synchronize":
        pull_request, new_revision = await _upsert_pull_request(
            session,
            repository=repository,
            fields=fields,
            create_revision=True,
        )
        if new_revision is None:
            return None
        await apply_resolution_status_for_synchronize(
            session,
            pull_request=pull_request,
            new_revision=new_revision,
        )
        await supersede_stale_generations_for_new_revision(
            session,
            pull_request_id=pull_request.id,
            keep_revision_id=new_revision.id,
        )
        return PullRequestWebhookResult(
            workspace_id=repository.workspace_id,
            revision_id=new_revision.id,
            new_revision=True,
            action=action,
        )

    if action == "edited":
        await _upsert_pull_request(
            session,
            repository=repository,
            fields=fields,
            create_revision=False,
        )
        return None

    if action in {"closed", "reopened", "converted_to_draft", "ready_for_review"}:
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
            return None
        existing.state = fields["state"]
        existing.title = fields["title"]
        existing.html_url = fields["html_url"]
        existing.is_draft = fields["is_draft"]
        existing.body = fields.get("body")
        await session.flush()

    return None


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
        _pull_request, _new_revision = await _upsert_pull_request(
            session,
            repository=repository,
            fields=fields,
            create_revision=False,
        )
        pull_request = _pull_request

    raw_review_id = review_payload.get("id")
    user = review_payload.get("user")
    state = review_payload.get("state")
    if (
        not isinstance(raw_review_id, int)
        or not isinstance(user, dict)
        or not isinstance(state, str)
    ):
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


async def apply_issue_comment_webhook_event(
    session: AsyncSession,
    payload: dict[str, Any],
) -> IssueCommentPipelineIntent | None:
    action = payload.get("action")
    if action != "created":
        if isinstance(action, str):
            logger.info("github_issue_comment_action_ignored", extra={"action": action})
        return None

    comment = payload.get("comment")
    issue = payload.get("issue")
    if not isinstance(comment, dict) or not isinstance(issue, dict):
        return None

    if issue.get("pull_request") is None:
        return None

    body = comment.get("body")
    if not isinstance(body, str) or not _REVY_REVIEW_COMMAND.search(body):
        return None

    user = comment.get("user")
    if isinstance(user, dict):
        login = user.get("login")
        bot_login = settings.revy_bot_login.strip()
        if isinstance(login, str) and bot_login and login.lower() == bot_login.lower():
            logger.info("github_issue_comment_bot_ignored", extra={"login": login})
            return None

    if issue.get("state") != "open":
        logger.info("github_issue_comment_not_open_ignored", extra={"state": issue.get("state")})
        return None

    repository = await _resolve_repository(session, payload)
    if repository is None:
        return None

    raw_pr_number = issue.get("number")
    if not isinstance(raw_pr_number, int):
        return None

    pull_request = await session.scalar(
        select(GitHubPullRequestORM).where(
            GitHubPullRequestORM.repository_id == repository.id,
            GitHubPullRequestORM.number == raw_pr_number,
        )
    )
    if pull_request is None:
        logger.warning(
            "github_issue_comment_orphan_pull_request",
            extra={"repository_id": str(repository.id), "number": raw_pr_number},
        )
        return None

    if pull_request.is_draft:
        logger.info("github_issue_comment_draft_ignored")
        return None

    if pull_request.state != GitHubPullRequestState.open:
        logger.info("github_issue_comment_closed_pr_ignored")
        return None

    revision = await _get_revision_for_head_sha(
        session,
        pull_request_id=pull_request.id,
        head_sha=pull_request.head_sha,
    )
    if revision is None:
        logger.warning(
            "github_issue_comment_revision_not_found",
            extra={"pull_request_id": str(pull_request.id), "head_sha": pull_request.head_sha},
        )
        return None

    return IssueCommentPipelineIntent(
        workspace_id=repository.workspace_id,
        revision_id=revision.id,
    )


async def get_github_pull_request(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
) -> GitHubPullRequestORM:
    pull_request = await session.scalar(
        select(GitHubPullRequestORM).where(
            GitHubPullRequestORM.id == pull_request_id,
            GitHubPullRequestORM.repository_id == repository_id,
            GitHubPullRequestORM.workspace_id == workspace_id,
        )
    )
    if pull_request is None:
        raise NotFoundError("Pull request not found")
    return pull_request


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
            | (
                (GitHubPullRequestORM.created_at == cursor_ts)
                & (GitHubPullRequestORM.id < cursor_id)
            )
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
