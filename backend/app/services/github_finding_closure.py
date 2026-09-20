# backend/app/services/github_finding_closure.py
"""Finding group closure — Pass 2 orchestration and Pass 3 verification judge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    GitHubFindingGroupState,
    GitHubJudgeOutcome,
    GitHubReviewRunStatus,
    JudgePurpose,
    ResolutionStatus,
)
from app.core.config import settings
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)
from app.core.logging import get_logger
from app.integrations import anthropic_review
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_finding_judge_outcome import GitHubFindingJudgeOutcomeORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM

# Re-export pure rules for existing callers.
from app.services.github_finding_closure_rules import (  # noqa: F401
    COMPARE_FAILED_REASON,
    apply_resolution_method_on_human_dismiss,
    apply_resolution_method_on_judge_dismiss,
    apply_resolution_method_on_verification_dismiss,
    closure_fields_for_absent_and_addressed,
    reopen_fields_for_re_report,
    should_close_absent_and_addressed,
    should_reopen_absent_and_addressed,
    should_skip_resolved_group_on_reconcile,
)
from app.services.github_finding_judge import (
    JudgeCandidateArtifact,
    _judge_failure_artifact,
    _judge_failure_log_extra,
    call_judge_with_optional_retry,
    judge_candidate_group_sql_predicate,
)
from app.services.github_finding_reconcile import _ensure_pull_request_access
from app.services.github_resolution_metrics import (
    get_intermediate_revision_ids_between,
    get_last_published_prior_revision,
    prior_publish_pairing_revision_ids,
)
from app.services.github_review import resolve_judge_code_context
from app.services.judge_prompt_context import judge_prompt_file_patch_chars
from app.services.model_policy import ModelRole, resolve_model

logger = get_logger(__name__)

VERIFICATION_JUDGE_MAX_PER_RUN = 5


@dataclass(frozen=True)
class VerificationJudgeResult:
    judged_count: int
    artifacts: list[Any]


def is_verification_escalation_candidate(
    *,
    group: GitHubFindingGroupORM,
    current_revision_id: UUID | None = None,
) -> bool:
    """FR-Q11: still_open escalation groups eligible for Pass 3 verification."""
    from app.services.github_finding_judge import is_judge_candidate

    if group.state != GitHubFindingGroupState.active:
        return False
    if group.resolution_status != ResolutionStatus.still_open:
        return False
    if group.closure_blocked_reason == COMPARE_FAILED_REASON:
        return False
    if current_revision_id is not None and group.last_seen_revision_id == current_revision_id:
        return False
    return is_judge_candidate(severity=group.severity, category=group.category)


def verification_escalation_candidate_sql_filters(
    *,
    pull_request_id: UUID,
    current_revision_id: UUID,
) -> list[Any]:
    """SQL filters mirroring is_verification_escalation_candidate (Pass 3 widen)."""
    return [
        GitHubFindingGroupORM.pull_request_id == pull_request_id,
        GitHubFindingGroupORM.state == GitHubFindingGroupState.active,
        GitHubFindingGroupORM.resolution_status == ResolutionStatus.still_open,
        or_(
            GitHubFindingGroupORM.closure_blocked_reason.is_(None),
            GitHubFindingGroupORM.closure_blocked_reason != COMPARE_FAILED_REASON,
        ),
        GitHubFindingGroupORM.last_seen_revision_id != current_revision_id,
        judge_candidate_group_sql_predicate(),
    ]


def pass3_verification_escalation_select(
    *,
    pull_request_id: UUID,
    current_revision_id: UUID,
    review_run_id: UUID,
    fingerprints_in_run: frozenset[str],
    limit: int,
):
    """Bounded, deterministic Pass 3 candidate query (SQL limit + order)."""
    if limit <= 0:
        raise ValueError("pass3_verification_escalation_limit_must_be_positive")
    filters = verification_escalation_candidate_sql_filters(
        pull_request_id=pull_request_id,
        current_revision_id=current_revision_id,
    )
    already_judged = select(GitHubFindingJudgeOutcomeORM.group_id).where(
        GitHubFindingJudgeOutcomeORM.review_run_id == review_run_id,
        GitHubFindingJudgeOutcomeORM.judge_purpose == JudgePurpose.verification,
    )
    filters.append(GitHubFindingGroupORM.id.not_in(already_judged))
    if fingerprints_in_run:
        filters.append(GitHubFindingGroupORM.fingerprint.not_in(fingerprints_in_run))
    return (
        select(GitHubFindingGroupORM)
        .where(*filters)
        .order_by(GitHubFindingGroupORM.last_seen_revision_id.asc())
        .limit(limit)
    )


async def _verification_judge_slots_remaining(
    session: AsyncSession,
    *,
    review_run_id: UUID,
) -> int:
    judged = await session.scalar(
        select(func.count())
        .select_from(GitHubFindingJudgeOutcomeORM)
        .where(
            GitHubFindingJudgeOutcomeORM.review_run_id == review_run_id,
            GitHubFindingJudgeOutcomeORM.judge_purpose == JudgePurpose.verification,
        )
    )
    return max(0, VERIFICATION_JUDGE_MAX_PER_RUN - int(judged or 0))


async def _load_prior_revision(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    current_revision: GitHubPullRequestRevisionORM,
) -> GitHubPullRequestRevisionORM | None:
    return await get_last_published_prior_revision(
        session,
        pull_request_id=pull_request_id,
        current_revision=current_revision,
    )


async def _bound_group_ids_this_run(
    session: AsyncSession, *, revision_id: UUID
) -> set[UUID]:
    """Group ids bound (last seen) at this revision via P0 reconcile."""
    result = await session.scalars(
        select(GitHubFindingGroupORM.id).where(
            GitHubFindingGroupORM.last_seen_revision_id == revision_id
        )
    )
    rows = list(result)
    return {row.id if hasattr(row, "id") else row for row in rows}


async def _this_run_finding_counts_by_file_category(
    session: AsyncSession, *, review_run_id: UUID
) -> dict[tuple[str, str], int]:
    """Count this-run findings per (file_path, category) key via SQL GROUP BY."""
    rows = await session.execute(
        select(
            GitHubFindingORM.file_path,
            GitHubFindingORM.category,
            func.count(),
        )
        .where(GitHubFindingORM.review_run_id == review_run_id)
        .group_by(GitHubFindingORM.file_path, GitHubFindingORM.category)
    )
    return {(row.file_path or "", row.category): row.count for row in rows}


async def _resolve_absent_paths(
    session: AsyncSession,
    *,
    revision: GitHubPullRequestRevisionORM,
    file_paths: frozenset[str] = frozenset(),
) -> set[str]:
    """Paths that have been removed or are absent at HEAD.

    Reuses the same resolution metrics path that Pass 1 stamps for
    deletion pushes. Returns empty set when compare fails (safe: compare
    failure is caught by closure_blocked_reason at the call site).
    """
    if not file_paths:
        return set()
    from app.services.github_path_hygiene import paths_absent_at_head

    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    if pull_request is None:
        return set()
    absent = await paths_absent_at_head(
        session,
        pull_request=pull_request,
        head_sha=revision.head_sha,
        file_paths=file_paths,
    )
    return {path for path, gone in absent.items() if gone}


async def _fingerprints_in_review_run(session: AsyncSession, *, review_run_id: UUID) -> set[str]:
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
    group_ids: list[UUID] = [f.group_id for f in findings if f.group_id is not None]
    group_map: dict[UUID, str] = {}
    if group_ids:
        group_result = await session.execute(
            select(GitHubFindingGroupORM.id, GitHubFindingGroupORM.fingerprint)
            .where(GitHubFindingGroupORM.id.in_(set(group_ids)))
        )
        for row in group_result:
            if row.fingerprint:
                group_map[row.id] = row.fingerprint

    for finding in findings:
        if finding.group_id is not None:
            fp = group_map.get(finding.group_id)
            if fp:
                fingerprints.add(fp)
    return fingerprints


async def apply_pass2_closure_for_review_run(
    session: AsyncSession,
    *,
    review_run_id: UUID,
) -> int:
    """Pass 2: H2-closure (P1) — close active groups when not bound this run and (path gone or zero findings in file+category)."""
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

    intermediate_revision_ids = await get_intermediate_revision_ids_between(
        session,
        pull_request_id=revision.pull_request_id,
        prior_revision=prior_revision,
        current_revision=revision,
    )
    pairing_revision_ids = prior_publish_pairing_revision_ids(
        prior_revision=prior_revision,
        intermediate_revision_ids=intermediate_revision_ids,
    )

    bound_group_ids = await _bound_group_ids_this_run(session, revision_id=revision.id)
    counts_by_key = await _this_run_finding_counts_by_file_category(
        session, review_run_id=review_run_id
    )

    groups = list(
        await session.scalars(
            select(GitHubFindingGroupORM).where(
                GitHubFindingGroupORM.pull_request_id == revision.pull_request_id,
                GitHubFindingGroupORM.state == GitHubFindingGroupState.active,
                or_(
                    GitHubFindingGroupORM.last_seen_revision_id.in_(pairing_revision_ids),
                    GitHubFindingGroupORM.resolution_status == ResolutionStatus.addressed,
                ),
            )
        )
    )
    group_file_paths = frozenset({g.file_path for g in groups if g.file_path})
    path_gone_paths = await _resolve_absent_paths(
        session, revision=revision, file_paths=group_file_paths
    )

    closed = 0
    for group in groups:
        file_key = (group.file_path or "", group.category)
        if not should_close_absent_and_addressed(
            state=group.state,
            bound_this_run=group.id in bound_group_ids,
            this_run_finding_count=counts_by_key.get(file_key, 0),
            path_gone=file_key[0] in path_gone_paths,
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

    fingerprints_in_run = frozenset(
        await _fingerprints_in_review_run(session, review_run_id=review_run_id)
    )
    remaining_slots = await _verification_judge_slots_remaining(
        session,
        review_run_id=review_run_id,
    )
    if remaining_slots == 0:
        return VerificationJudgeResult(judged_count=0, artifacts=[])

    loaded = list(
        await session.scalars(
            pass3_verification_escalation_select(
                pull_request_id=revision.pull_request_id,
                current_revision_id=revision.id,
                review_run_id=review_run_id,
                fingerprints_in_run=fingerprints_in_run,
                limit=remaining_slots,
            )
        )
    )
    escalation_groups = [
        group
        for group in loaded
        if is_verification_escalation_candidate(
            group=group,
            current_revision_id=revision.id,
        )
        and group.fingerprint not in fingerprints_in_run
    ]
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
        for group in escalation_groups:
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
            patch_chars = judge_prompt_file_patch_chars(
                evidence_snippet,
                push_delta_patch or None,
            )
            raw: dict[str, Any] | None = None
            outcome_str: str | None = None
            notes: str | None = None
            retry_count = 0

            try:
                raw, retry_count = await call_judge_with_optional_retry(
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
                    extra=_judge_failure_log_extra(group.id, exc),
                )
                artifacts.append(
                    _judge_failure_artifact(
                        group_id=group.id,
                        evidence_snippet=evidence_snippet,
                        user_prompt=user_prompt,
                        file_patch_chars=patch_chars,
                        exc=exc,
                        retry_count=getattr(exc, "judge_retry_count", retry_count),
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

            input_tokens, output_tokens = anthropic_review.judge_token_usage_from_transport()
            artifacts.append(
                JudgeCandidateArtifact(
                    group_id=group.id,
                    evidence_snippet=evidence_snippet,
                    user_prompt=user_prompt,
                    raw_response=anthropic_review.judge_raw_response_with_usage(raw),
                    outcome=outcome_str,
                    file_patch_chars=patch_chars,
                    retry_count=retry_count,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            )
            judged += 1

    await session.flush()
    return VerificationJudgeResult(judged_count=judged, artifacts=artifacts)


async def dismiss_finding_group(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    group_id: UUID,
) -> GitHubFindingGroupORM:
    """Human dismiss — FR-Q5 / P4.1."""
    await _ensure_pull_request_access(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
    )
    group = await session.get(GitHubFindingGroupORM, group_id)
    if (
        group is None
        or group.workspace_id != workspace_id
        or group.pull_request_id != pull_request_id
    ):
        raise NotFoundError("Finding group not found")
    if group.state != GitHubFindingGroupState.active:
        raise ConflictError(
            message="Finding group is not active",
            error_code="group_not_active",
        )

    head_revision = await session.scalar(
        select(GitHubPullRequestRevisionORM)
        .where(GitHubPullRequestRevisionORM.pull_request_id == pull_request_id)
        .order_by(GitHubPullRequestRevisionORM.revision_number.desc())
        .limit(1)
    )
    if head_revision is None:
        raise NotFoundError("Pull request revision not found")

    fields = apply_resolution_method_on_human_dismiss(resolved_at_revision_id=head_revision.id)
    for key, value in fields.items():
        setattr(group, key, value)
    await session.flush()
    return group
