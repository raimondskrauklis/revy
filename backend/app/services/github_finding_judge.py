# backend/app/services/github_finding_judge.py
"""GitHub finding judge escalation — R5."""
from __future__ import annotations

from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubJudgeOutcome,
    GitHubReviewRunStatus,
)
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.core.logging import get_logger
from app.integrations import anthropic_review, llm_dispatch
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_finding_judge_outcome import GitHubFindingJudgeOutcomeORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_finding_reconcile import severity_rank
from app.services.model_policy import ModelRole, resolve_model

logger = get_logger(__name__)

JUDGE_MAX_PER_RUN = 10


def is_judge_candidate(*, severity: FindingSeverity, category: FindingCategory) -> bool:
    if severity in (FindingSeverity.error, FindingSeverity.critical):
        return True
    return (
        category == FindingCategory.security
        and severity_rank(severity) >= severity_rank(FindingSeverity.warning)
    )


def _build_judge_prompt(*, group: GitHubFindingGroupORM) -> str:
    return (
        f"Title: {group.title}\n"
        f"Severity: {group.severity.value}\n"
        f"Category: {group.category.value}\n"
        f"File: {group.file_path or 'n/a'}\n"
        f"Message: {group.message}\n"
    )


async def run_judge_for_review_run(session: AsyncSession, *, review_run_id: UUID) -> int:
    """Run judge on escalation candidates. Returns outcome count (0 when skipped)."""
    if not settings.judge_llm_enabled():
        return 0

    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None or run.status != GitHubReviewRunStatus.completed:
        return 0

    findings = list(
        await session.scalars(
            select(GitHubFindingORM).where(
                GitHubFindingORM.review_run_id == review_run_id,
                GitHubFindingORM.group_id.is_not(None),
            )
        )
    )

    candidates: list[tuple[GitHubFindingORM, GitHubFindingGroupORM]] = []
    for finding in findings:
        if finding.group_id is None:
            continue
        group = await session.get(GitHubFindingGroupORM, finding.group_id)
        if group is None or group.state == GitHubFindingGroupState.resolved:
            continue
        if not is_judge_candidate(severity=finding.severity, category=finding.category):
            continue
        candidates.append((finding, group))

    judged = 0
    try:
        model_ref = await resolve_model(session, run.workspace_id, ModelRole.judge)
    except (ServiceUnavailableError, ValidationError) as exc:
        logger.error(
            "github_finding_judge_model_resolve_failed",
            extra={"review_run_id": str(review_run_id), "error": str(exc)},
        )
        return 0
    async with httpx.AsyncClient(timeout=float(settings.revy_revision_timeout_standard_seconds)) as client:
        for _finding, group in candidates[:JUDGE_MAX_PER_RUN]:
            existing = await session.scalar(
                select(GitHubFindingJudgeOutcomeORM.id).where(
                    GitHubFindingJudgeOutcomeORM.review_run_id == review_run_id,
                    GitHubFindingJudgeOutcomeORM.group_id == group.id,
                )
            )
            if existing is not None:
                continue

            try:
                raw = await llm_dispatch.call_judge_llm(
                    client,
                    model_ref=model_ref,
                    user_prompt=_build_judge_prompt(group=group),
                    timeout_seconds=float(settings.revy_revision_timeout_standard_seconds),
                )
                outcome_str, notes = anthropic_review.parse_judge_outcome(raw)
            except (httpx.HTTPError, ValueError, ServiceUnavailableError) as exc:
                logger.error(
                    "github_finding_judge_failed",
                    extra={"group_id": str(group.id), "error": str(exc)},
                )
                continue

            outcome = GitHubJudgeOutcome(outcome_str)
            session.add(
                GitHubFindingJudgeOutcomeORM(
                    group_id=group.id,
                    review_run_id=review_run_id,
                    workspace_id=run.workspace_id,
                    outcome=outcome,
                    judge_provider=model_ref.provider,
                    judge_model_id=model_ref.model_id,
                    judge_notes=notes,
                )
            )

            if outcome == GitHubJudgeOutcome.dismissed:
                group.state = GitHubFindingGroupState.resolved
            elif outcome == GitHubJudgeOutcome.modified:
                group.severity = FindingSeverity.warning

            judged += 1

    await session.flush()
    return judged
