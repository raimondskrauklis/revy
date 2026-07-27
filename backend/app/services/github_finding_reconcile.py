# backend/app/services/github_finding_reconcile.py
"""GitHub finding reconciliation — R5."""
from __future__ import annotations

import hashlib
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubReviewRunStatus,
    stored_enum_value,
)
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
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM
from app.models.github_review_run import GitHubReviewRunORM
from app.schemas.github_review import ReconciledFindingResponse

logger = get_logger(__name__)

_FINGERPRINT_SEP = "\x1f"


def start_line_key(start_line: int | None) -> str:
    return str(start_line) if start_line is not None else "0"


def compute_fingerprint(
    *,
    workspace_id: UUID,
    pull_request_id: UUID,
    file_path: str | None,
    category: FindingCategory | str,
    title: str,
    start_line: int | None,
) -> str:
    normalized_title = title.strip()
    payload = _FINGERPRINT_SEP.join(
        [
            str(workspace_id),
            str(pull_request_id),
            file_path or "",
            stored_enum_value(category),
            normalized_title,
            start_line_key(start_line),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def _mark_superseded_peers(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    file_path: str | None,
    category: FindingCategory,
    revision_id: UUID,
    exclude_group_id: UUID,
) -> None:
    if not file_path:
        return

    peers = list(
        await session.scalars(
            select(GitHubFindingGroupORM).where(
                GitHubFindingGroupORM.pull_request_id == pull_request_id,
                GitHubFindingGroupORM.file_path == file_path,
                GitHubFindingGroupORM.category == category,
                GitHubFindingGroupORM.state == GitHubFindingGroupState.active,
                GitHubFindingGroupORM.id != exclude_group_id,
            )
        )
    )
    for peer in peers:
        if peer.last_seen_revision_id != revision_id:
            peer.state = GitHubFindingGroupState.superseded


async def reconcile_review_run(session: AsyncSession, *, review_run_id: UUID) -> list[UUID]:
    """Link run findings to stable groups. Returns group ids linked in this run."""
    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None:
        logger.warning("reconcile_review_run_missing", extra={"review_run_id": str(review_run_id)})
        return []
    if run.status != GitHubReviewRunStatus.completed:
        return []

    revision = await session.get(GitHubPullRequestRevisionORM, run.revision_id)
    if revision is None:
        return []

    pull_request_id = revision.pull_request_id
    findings = list(
        await session.scalars(
            select(GitHubFindingORM).where(GitHubFindingORM.review_run_id == review_run_id)
        )
    )

    linked_group_ids: list[UUID] = []
    for finding in findings:
        fingerprint = compute_fingerprint(
            workspace_id=run.workspace_id,
            pull_request_id=pull_request_id,
            file_path=finding.file_path,
            category=finding.category,
            title=finding.title,
            start_line=finding.start_line,
        )

        group = await session.scalar(
            select(GitHubFindingGroupORM).where(
                GitHubFindingGroupORM.pull_request_id == pull_request_id,
                GitHubFindingGroupORM.fingerprint == fingerprint,
            )
        )

        if group is None:
            group = GitHubFindingGroupORM(
                workspace_id=run.workspace_id,
                pull_request_id=pull_request_id,
                fingerprint=fingerprint,
                state=GitHubFindingGroupState.active,
                severity=finding.severity,
                category=finding.category,
                title=finding.title,
                message=finding.message,
                file_path=finding.file_path,
                last_seen_revision_id=revision.id,
            )
            session.add(group)
            await session.flush()
            await _mark_superseded_peers(
                session,
                pull_request_id=pull_request_id,
                file_path=finding.file_path,
                category=finding.category,
                revision_id=revision.id,
                exclude_group_id=group.id,
            )
        elif group.state == GitHubFindingGroupState.resolved:
            pass
        else:
            group.last_seen_revision_id = revision.id
            group.severity = finding.severity
            group.category = finding.category
            group.title = finding.title
            group.message = finding.message
            group.file_path = finding.file_path
            group.state = GitHubFindingGroupState.active
            await _mark_superseded_peers(
                session,
                pull_request_id=pull_request_id,
                file_path=finding.file_path,
                category=finding.category,
                revision_id=revision.id,
                exclude_group_id=group.id,
            )

        finding.group_id = group.id
        linked_group_ids.append(group.id)

    await session.flush()
    return linked_group_ids


def severity_rank(severity: FindingSeverity | str) -> int:
    order = {
        FindingSeverity.info: 0,
        FindingSeverity.warning: 1,
        FindingSeverity.error: 2,
        FindingSeverity.critical: 3,
    }
    if isinstance(severity, str):
        severity = FindingSeverity(severity)
    return order[severity]


async def _ensure_pull_request_access(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
) -> None:
    pr_key = await session.scalar(
        select(GitHubPullRequestORM.id)
        .join(
            GitHubRepositoryORM,
            GitHubPullRequestORM.repository_id == GitHubRepositoryORM.id,
        )
        .where(
            GitHubPullRequestORM.id == pull_request_id,
            GitHubPullRequestORM.repository_id == repository_id,
            GitHubPullRequestORM.workspace_id == workspace_id,
            GitHubRepositoryORM.id == repository_id,
            GitHubRepositoryORM.workspace_id == workspace_id,
        )
    )
    if pr_key is None:
        raise NotFoundError("Pull request not found")


async def list_reconciled_finding_groups(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    params: CursorParams,
) -> CursorResponse[ReconciledFindingResponse]:
    await _ensure_pull_request_access(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
    )

    stmt = select(GitHubFindingGroupORM).where(
        GitHubFindingGroupORM.workspace_id == workspace_id,
        GitHubFindingGroupORM.pull_request_id == pull_request_id,
        GitHubFindingGroupORM.state != GitHubFindingGroupState.superseded,
    )

    if params.cursor:
        try:
            cursor_ts, cursor_id = decode_cursor(params.cursor)
        except InvalidCursorError as exc:
            raise ValidationError(message="Invalid cursor", field="cursor") from exc
        stmt = stmt.where(
            (GitHubFindingGroupORM.created_at < cursor_ts)
            | (
                (GitHubFindingGroupORM.created_at == cursor_ts)
                & (GitHubFindingGroupORM.id < cursor_id)
            )
        )

    stmt = stmt.order_by(
        GitHubFindingGroupORM.created_at.desc(),
        GitHubFindingGroupORM.id.desc(),
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
        items=[ReconciledFindingResponse.model_validate(row) for row in rows],
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )
