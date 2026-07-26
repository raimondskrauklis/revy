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
    GitHubReviewJudgeStatus,
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
from app.services.model_policy import ModelRef, ModelRole, resolve_model

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


async def _load_judge_candidates(
    session: AsyncSession,
    *,
    review_run_id: UUID,
) -> tuple[GitHubReviewRunORM | None, list[tuple[GitHubFindingORM, GitHubFindingGroupORM]]]:
    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None or run.status != GitHubReviewRunStatus.completed:
        return run, []

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

    return run, candidates


async def _run_judge_llm_loop(
    session: AsyncSession,
    *,
    run: GitHubReviewRunORM,
    review_run_id: UUID,
    candidates: list[tuple[GitHubFindingORM, GitHubFindingGroupORM]],
    model_ref: ModelRef,
) -> int:
    judged = 0
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

    return judged


async def _review_run_has_judge_outcomes(session: AsyncSession, *, review_run_id: UUID) -> bool:
    existing = await session.scalar(
        select(GitHubFindingJudgeOutcomeORM.id)
        .where(GitHubFindingJudgeOutcomeORM.review_run_id == review_run_id)
        .limit(1)
    )
    return existing is not None


async def record_review_run_judge_status(
    session: AsyncSession,
    *,
    review_run_id: UUID,
) -> int:
    """Count escalation candidates, persist judge status, run judge when applicable."""
    run, candidates = await _load_judge_candidates(session, review_run_id=review_run_id)
    if run is None:
        return 0

    candidate_count = len(candidates)
    run.judge_escalation_candidate_count = candidate_count

    if run.status != GitHubReviewRunStatus.completed or candidate_count == 0:
        if candidate_count == 0 and await _review_run_has_judge_outcomes(
            session, review_run_id=review_run_id
        ):
            run.judge_status = GitHubReviewJudgeStatus.completed
        else:
            run.judge_status = GitHubReviewJudgeStatus.not_applicable
        await session.flush()
        return 0

    if not settings.judge_llm_enabled():
        if await _review_run_has_judge_outcomes(session, review_run_id=review_run_id):
            run.judge_status = GitHubReviewJudgeStatus.completed
        else:
            run.judge_status = GitHubReviewJudgeStatus.skipped_disabled
        await session.flush()
        return 0

    try:
        model_ref = await resolve_model(session, run.workspace_id, ModelRole.judge)
    except (ServiceUnavailableError, ValidationError) as exc:
        logger.error(
            "github_finding_judge_model_resolve_failed",
            extra={"review_run_id": str(review_run_id), "error": str(exc)},
        )
        if await _review_run_has_judge_outcomes(session, review_run_id=review_run_id):
            run.judge_status = GitHubReviewJudgeStatus.completed
        else:
            run.judge_status = GitHubReviewJudgeStatus.skipped_unavailable
        await session.flush()
        return 0

    judged = await _run_judge_llm_loop(
        session,
        run=run,
        review_run_id=review_run_id,
        candidates=candidates,
        model_ref=model_ref,
    )
    run.judge_status = GitHubReviewJudgeStatus.completed
    await session.flush()
    return judged


async def run_judge_for_review_run(session: AsyncSession, *, review_run_id: UUID) -> int:
    """Run judge on escalation candidates. Returns outcome count (0 when skipped)."""
    return await record_review_run_judge_status(session, review_run_id=review_run_id)
