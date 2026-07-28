# backend/app/services/github_finding_judge.py
"""GitHub finding judge escalation — R5."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
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
    stored_enum_value,
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

_GROUNDING_WITH_EVIDENCE = (
    "Grounding (E2): Dismiss or weaken the finding if the claim is not entailed by "
    "the evidence excerpt. Uphold only when the excerpt supports the severity and message."
)
_GROUNDING_WITHOUT_EVIDENCE = (
    "Grounding (E2): No evidence excerpt was captured. Judge conservatively; dismiss "
    "if the claim cannot be verified from the message alone."
)


@dataclass(frozen=True)
class JudgeCandidateArtifact:
    group_id: UUID
    evidence_snippet: str | None
    user_prompt: str
    raw_response: dict[str, Any] | None
    outcome: str | None


def is_judge_candidate(*, severity: FindingSeverity, category: FindingCategory) -> bool:
    if severity in (FindingSeverity.error, FindingSeverity.critical):
        return True
    return (
        category == FindingCategory.security
        and severity_rank(severity) >= severity_rank(FindingSeverity.warning)
    )


def _build_judge_prompt(
    *,
    group: GitHubFindingGroupORM,
    evidence_snippet: str | None,
    start_line: int | None = None,
    end_line: int | None = None,
    suggestion: str | None = None,
) -> str:
    parts = [
        f"Title: {group.title}",
        f"Severity: {stored_enum_value(group.severity)}",
        f"Category: {stored_enum_value(group.category)}",
        f"File: {group.file_path or 'n/a'}",
        f"Message: {group.message}",
    ]
    if start_line is not None:
        line_ref = str(start_line)
        if end_line is not None and end_line != start_line:
            line_ref = f"{start_line}-{end_line}"
        parts.append(f"Line: {line_ref}")
    if suggestion:
        parts.append(f"Suggested fix: {suggestion}")
    if evidence_snippet:
        parts.extend(
            [
                "",
                "Evidence (code excerpt from diff or retrieval):",
                evidence_snippet,
                "",
                _GROUNDING_WITH_EVIDENCE,
            ]
        )
    else:
        parts.extend(["", _GROUNDING_WITHOUT_EVIDENCE])
    return "\n".join(parts)


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
    artifacts_out: list[JudgeCandidateArtifact] | None = None,
) -> int:
    judged = 0
    async with httpx.AsyncClient(timeout=float(settings.revy_revision_timeout_standard_seconds)) as client:
        for finding, group in candidates[:JUDGE_MAX_PER_RUN]:
            existing = await session.scalar(
                select(GitHubFindingJudgeOutcomeORM.id).where(
                    GitHubFindingJudgeOutcomeORM.review_run_id == review_run_id,
                    GitHubFindingJudgeOutcomeORM.group_id == group.id,
                )
            )
            if existing is not None:
                continue

            user_prompt = _build_judge_prompt(
                group=group,
                evidence_snippet=finding.evidence_snippet,
                start_line=finding.start_line,
                end_line=finding.end_line,
                suggestion=finding.suggestion,
            )
            raw: dict[str, Any] | None = None
            outcome_str: str | None = None
            notes: str | None = None

            try:
                raw = await llm_dispatch.call_judge_llm(
                    client,
                    model_ref=model_ref,
                    user_prompt=user_prompt,
                    timeout_seconds=float(settings.revy_revision_timeout_standard_seconds),
                )
                outcome_str, notes = anthropic_review.parse_judge_outcome(raw)
            except (httpx.HTTPError, ValueError, ServiceUnavailableError) as exc:
                logger.error(
                    "github_finding_judge_failed",
                    extra={"group_id": str(group.id), "error": str(exc)},
                )
                if artifacts_out is not None:
                    artifacts_out.append(
                        JudgeCandidateArtifact(
                            group_id=group.id,
                            evidence_snippet=finding.evidence_snippet,
                            user_prompt=user_prompt,
                            raw_response=None,
                            outcome=None,
                        )
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

            if artifacts_out is not None:
                artifacts_out.append(
                    JudgeCandidateArtifact(
                        group_id=group.id,
                        evidence_snippet=finding.evidence_snippet,
                        user_prompt=user_prompt,
                        raw_response=raw,
                        outcome=outcome_str,
                    )
                )
            judged += 1

    return judged


async def _review_run_has_judge_outcomes(session: AsyncSession, *, review_run_id: UUID) -> bool:
    existing = await session.scalar(
        select(GitHubFindingJudgeOutcomeORM.id)
        .where(GitHubFindingJudgeOutcomeORM.review_run_id == review_run_id)
        .limit(1)
    )
    return existing is not None


async def _judge_candidates_missing_outcome(
    session: AsyncSession,
    *,
    review_run_id: UUID,
    candidates: list[tuple[GitHubFindingORM, GitHubFindingGroupORM]],
) -> bool:
    for _finding, group in candidates:
        if group.state == GitHubFindingGroupState.resolved:
            continue
        existing = await session.scalar(
            select(GitHubFindingJudgeOutcomeORM.id).where(
                GitHubFindingJudgeOutcomeORM.review_run_id == review_run_id,
                GitHubFindingJudgeOutcomeORM.group_id == group.id,
            )
        )
        if existing is None:
            return True
    return False


async def record_review_run_judge_status(
    session: AsyncSession,
    *,
    review_run_id: UUID,
    artifacts_out: list[JudgeCandidateArtifact] | None = None,
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
        artifacts_out=artifacts_out,
    )
    await session.flush()
    if await _judge_candidates_missing_outcome(
        session,
        review_run_id=review_run_id,
        candidates=candidates,
    ):
        run.judge_status = GitHubReviewJudgeStatus.skipped_unavailable
    else:
        run.judge_status = GitHubReviewJudgeStatus.completed
    await session.flush()
    return judged


async def run_judge_for_review_run(session: AsyncSession, *, review_run_id: UUID) -> int:
    """Run judge on escalation candidates. Returns outcome count (0 when skipped)."""
    return await record_review_run_judge_status(session, review_run_id=review_run_id)
