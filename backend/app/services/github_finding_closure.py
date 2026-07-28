# backend/app/services/github_finding_closure.py
"""Finding group closure — Pass 2 rules and Pass 3 verification judge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    GitHubFindingGroupState,
    GitHubJudgeOutcome,
    GitHubReviewRunStatus,
    JudgePurpose,
    ResolutionMethod,
    ResolutionStatus,
)
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.core.logging import get_logger
from app.integrations import anthropic_review, llm_dispatch
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_finding_judge_outcome import GitHubFindingJudgeOutcomeORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_review import resolve_judge_code_context
from app.services.model_policy import ModelRole, resolve_model

logger = get_logger(__name__)

COMPARE_FAILED_REASON = "compare_failed"
VERIFICATION_JUDGE_MAX_PER_RUN = 5


@dataclass(frozen=True)
class VerificationJudgeResult:
    judged_count: int
    artifacts: list[Any]


def should_close_absent_and_addressed(
    *,
    state: GitHubFindingGroupState,
    fingerprint_in_current_run: bool,
    resolution_status: ResolutionStatus | None,
    closure_blocked_reason: str | None,
) -> bool:
    """FR-Q3: absent fingerprint + addressed on prior revision, compare succeeded."""
    if state != GitHubFindingGroupState.active:
        return False
    if fingerprint_in_current_run:
        return False
    if resolution_status != ResolutionStatus.addressed:
        return False
    return closure_blocked_reason is None


def closure_fields_for_absent_and_addressed(
    *,
    resolved_at_revision_id: UUID,
) -> dict[str, object]:
    return {
        "state": GitHubFindingGroupState.resolved,
        "resolution_method": ResolutionMethod.absent_and_addressed,
        "resolved_at_revision_id": resolved_at_revision_id,
        "closure_blocked_reason": None,
    }


def apply_resolution_method_on_judge_dismiss(
    *,
    outcome: GitHubJudgeOutcome,
    resolved_at_revision_id: UUID,
) -> dict[str, object] | None:
    """Discovery judge dismiss → resolved + judge_dismissed."""
    if outcome != GitHubJudgeOutcome.dismissed:
        return None
    return {
        "state": GitHubFindingGroupState.resolved,
        "resolution_method": ResolutionMethod.judge_dismissed,
        "resolved_at_revision_id": resolved_at_revision_id,
        "closure_blocked_reason": None,
    }


def apply_resolution_method_on_verification_dismiss(
    *,
    outcome: GitHubJudgeOutcome,
    resolved_at_revision_id: UUID,
) -> dict[str, object] | None:
    if outcome != GitHubJudgeOutcome.dismissed:
        return None
    return {
        "state": GitHubFindingGroupState.resolved,
        "resolution_method": ResolutionMethod.verification_dismissed,
        "resolved_at_revision_id": resolved_at_revision_id,
        "closure_blocked_reason": None,
    }


def should_reopen_absent_and_addressed(
    *,
    resolution_method: ResolutionMethod | None,
    fingerprint_in_current_run: bool,
) -> bool:
    """FR-Q13: re-report same fingerprint after heuristic-only closure."""
    if resolution_method != ResolutionMethod.absent_and_addressed:
        return False
    return fingerprint_in_current_run


def reopen_fields_for_re_report() -> dict[str, object]:
    return {
        "state": GitHubFindingGroupState.active,
        "resolution_method": None,
        "resolved_at_revision_id": None,
        "closure_blocked_reason": None,
    }


def should_skip_resolved_group_on_reconcile(
    *,
    state: GitHubFindingGroupState,
    resolution_method: ResolutionMethod | None,
) -> bool:
    """Skip reconcile updates for terminal dismiss paths and legacy resolved rows (method NULL)."""
    if state != GitHubFindingGroupState.resolved:
        return False
    return resolution_method in (
        ResolutionMethod.judge_dismissed,
        ResolutionMethod.verification_dismissed,
        ResolutionMethod.human_dismissed,
        None,  # legacy pre-0028 resolved groups — do not re-open
    )


def is_verification_escalation_candidate(
    *,
    group: GitHubFindingGroupORM,
) -> bool:
    """FR-Q11: still_open escalation groups eligible for Pass 3 verification."""
    from app.services.github_finding_judge import is_judge_candidate

    if group.resolution_status != ResolutionStatus.still_open:
        return False
    if group.closure_blocked_reason == COMPARE_FAILED_REASON:
        return False
    return is_judge_candidate(severity=group.severity, category=group.category)


async def _load_prior_revision(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    current_revision: GitHubPullRequestRevisionORM,
) -> GitHubPullRequestRevisionORM | None:
    return await session.scalar(
        select(GitHubPullRequestRevisionORM).where(
            GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            GitHubPullRequestRevisionORM.revision_number == current_revision.revision_number - 1,
        )
    )


async def _fingerprints_in_review_run(session: AsyncSession, *, review_run_id: UUID) -> set[str]:
    from app.services.github_finding_reconcile import compute_fingerprint

    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None:
        return set()

    revision = await session.get(GitHubPullRequestRevisionORM, run.revision_id)
    if revision is None:
        return set()

    findings = list(
        await session.scalars(
            select(GitHubFindingORM).where(GitHubFindingORM.review_run_id == review_run_id)
        )
    )
    fingerprints: set[str] = set()
    for finding in findings:
        fingerprints.add(
            compute_fingerprint(
                workspace_id=run.workspace_id,
                pull_request_id=revision.pull_request_id,
                file_path=finding.file_path,
                category=finding.category,
                title=finding.title,
                start_line=finding.start_line,
            )
        )
    return fingerprints


async def apply_pass2_closure_for_review_run(
    session: AsyncSession,
    *,
    review_run_id: UUID,
) -> int:
    """Pass 2: close groups absent from run with resolution_status=addressed."""
    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None or run.status != GitHubReviewRunStatus.completed:
        return 0

    revision = await session.get(GitHubPullRequestRevisionORM, run.revision_id)
    if revision is None:
        return 0

    prior_revision = await _load_prior_revision(
        session,
        pull_request_id=revision.pull_request_id,
        current_revision=revision,
    )
    if prior_revision is None:
        return 0

    fingerprints_in_run = await _fingerprints_in_review_run(session, review_run_id=review_run_id)
    groups = list(
        await session.scalars(
            select(GitHubFindingGroupORM).where(
                GitHubFindingGroupORM.pull_request_id == revision.pull_request_id,
                GitHubFindingGroupORM.last_seen_revision_id == prior_revision.id,
                GitHubFindingGroupORM.state == GitHubFindingGroupState.active,
            )
        )
    )

    closed = 0
    for group in groups:
        if not should_close_absent_and_addressed(
            state=group.state,
            fingerprint_in_current_run=group.fingerprint in fingerprints_in_run,
            resolution_status=group.resolution_status,
            closure_blocked_reason=group.closure_blocked_reason,
        ):
            continue
        fields = closure_fields_for_absent_and_addressed(resolved_at_revision_id=revision.id)
        for key, value in fields.items():
            setattr(group, key, value)
        closed += 1

    await session.flush()
    return closed


async def verify_still_open_escalation_groups(
    session: AsyncSession,
    *,
    review_run_id: UUID,
) -> VerificationJudgeResult:
    """Pass 3: verification judge on FR-Q11 escalation groups (cap 5/run)."""
    from app.services.github_compare_patches import fetch_compare_patches
    from app.services.github_finding_judge import JudgeCandidateArtifact

    if not settings.judge_llm_enabled():
        return VerificationJudgeResult(judged_count=0, artifacts=[])

    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None or run.status != GitHubReviewRunStatus.completed:
        return VerificationJudgeResult(judged_count=0, artifacts=[])

    revision = await session.get(GitHubPullRequestRevisionORM, run.revision_id)
    if revision is None:
        return VerificationJudgeResult(judged_count=0, artifacts=[])

    prior_revision = await _load_prior_revision(
        session,
        pull_request_id=revision.pull_request_id,
        current_revision=revision,
    )
    if prior_revision is None:
        return VerificationJudgeResult(judged_count=0, artifacts=[])

    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    if pull_request is None:
        return VerificationJudgeResult(judged_count=0, artifacts=[])

    compare_result = await fetch_compare_patches(
        session,
        pull_request=pull_request,
        base_sha=prior_revision.head_sha,
        head_sha=revision.head_sha,
        log_event="verification_compare_patches_failed",
    )
    if compare_result.compare_failed:
        return VerificationJudgeResult(judged_count=0, artifacts=[])

    candidates = list(
        await session.scalars(
            select(GitHubFindingGroupORM).where(
                GitHubFindingGroupORM.pull_request_id == revision.pull_request_id,
                GitHubFindingGroupORM.last_seen_revision_id == prior_revision.id,
                GitHubFindingGroupORM.state == GitHubFindingGroupState.active,
            )
        )
    )
    escalation_groups = [group for group in candidates if is_verification_escalation_candidate(group=group)]
    if not escalation_groups:
        return VerificationJudgeResult(judged_count=0, artifacts=[])

    try:
        model_ref = await resolve_model(session, run.workspace_id, ModelRole.judge)
    except (ServiceUnavailableError, ValidationError) as exc:
        logger.warning(
            "verification_judge_model_resolve_failed",
            extra={"review_run_id": str(review_run_id), "error": str(exc)},
        )
        return VerificationJudgeResult(judged_count=0, artifacts=[])

    artifacts: list[JudgeCandidateArtifact] = []
    judged = 0
    async with httpx.AsyncClient(timeout=float(settings.revy_revision_timeout_standard_seconds)) as client:
        for group in escalation_groups[:VERIFICATION_JUDGE_MAX_PER_RUN]:
            existing = await session.scalar(
                select(GitHubFindingJudgeOutcomeORM.id).where(
                    GitHubFindingJudgeOutcomeORM.review_run_id == review_run_id,
                    GitHubFindingJudgeOutcomeORM.group_id == group.id,
                    GitHubFindingJudgeOutcomeORM.judge_purpose == JudgePurpose.verification,
                )
            )
            if existing is not None:
                continue

            finding = await session.scalar(
                select(GitHubFindingORM)
                .where(GitHubFindingORM.group_id == group.id)
                .order_by(GitHubFindingORM.created_at.desc())
                .limit(1)
            )
            push_delta_patch = (
                compare_result.patches_by_file.get(group.file_path or "", "")
                if group.file_path
                else ""
            )
            evidence_snippet = finding.evidence_snippet if finding is not None else None
            if finding is not None and not evidence_snippet:
                code_context = resolve_judge_code_context(
                    file_path=finding.file_path,
                    start_line=finding.start_line,
                    patches_by_file=compare_result.patches_by_file,
                    supplemental_top_by_file={},
                )
                evidence_snippet = code_context.evidence_snippet

            user_prompt = anthropic_review.build_verification_judge_prompt(
                group=group,
                push_delta_patch=push_delta_patch or None,
                evidence_snippet=evidence_snippet,
                start_line=finding.start_line if finding is not None else None,
                end_line=finding.end_line if finding is not None else None,
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
                    system_prompt=anthropic_review.VERIFICATION_JUDGE_SYSTEM_PROMPT,
                )
                outcome_str, notes = anthropic_review.parse_judge_outcome(raw)
                if outcome_str == GitHubJudgeOutcome.modified.value:
                    raise ValueError("verification_judge_outcome_modified")
            except (httpx.HTTPError, ValueError, ServiceUnavailableError) as exc:
                logger.error(
                    "verification_judge_failed",
                    extra={"group_id": str(group.id), "error": str(exc)},
                )
                artifacts.append(
                    JudgeCandidateArtifact(
                        group_id=group.id,
                        evidence_snippet=evidence_snippet,
                        user_prompt=user_prompt,
                        raw_response=None,
                        outcome=None,
                        file_patch_chars=len(push_delta_patch) if push_delta_patch else None,
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
                    judge_purpose=JudgePurpose.verification,
                    judge_provider=model_ref.provider,
                    judge_model_id=model_ref.model_id,
                    judge_notes=notes,
                )
            )
            dismiss_fields = apply_resolution_method_on_verification_dismiss(
                outcome=outcome,
                resolved_at_revision_id=revision.id,
            )
            if dismiss_fields is not None:
                for key, value in dismiss_fields.items():
                    setattr(group, key, value)

            artifacts.append(
                JudgeCandidateArtifact(
                    group_id=group.id,
                    evidence_snippet=evidence_snippet,
                    user_prompt=user_prompt,
                    raw_response=raw,
                    outcome=outcome_str,
                    file_patch_chars=len(push_delta_patch) if push_delta_patch else None,
                )
            )
            judged += 1

    await session.flush()
    return VerificationJudgeResult(judged_count=judged, artifacts=artifacts)
