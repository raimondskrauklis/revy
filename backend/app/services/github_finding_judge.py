# backend/app/services/github_finding_judge.py
"""GitHub finding judge escalation — R5."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import and_, or_, select
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
from app.integrations.judge_llm_errors import JudgeParseError, judge_failure_trace_fields
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_finding_judge_outcome import GitHubFindingJudgeOutcomeORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.engineering_context.pack import (
    EngineeringContextPack,
    build_engineering_context_pack,
)
from app.services.github_compare_patches import fetch_compare_review_context
from app.services.github_finding_closure_rules import apply_resolution_method_on_judge_dismiss
from app.services.github_finding_reconcile import severity_rank
from app.services.github_review import resolve_judge_code_context
from app.services.judge_prompt_context import (
    format_judge_engineering_context,
    judge_prompt_file_patch_chars,
    resolve_judge_prompt_file_patch,
)
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
    file_patch_chars: int | None = None
    lock_ids_cited: list[str] | None = None
    raw_response_text: str | None = None
    parse_error: str | None = None
    retry_count: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None


_JUDGE_RETRY_SCHEMA_REMINDER = (
    'Return JSON only: {"outcome":"upheld|dismissed|modified","notes":"brief rationale"}'
)


async def call_judge_with_optional_retry(
    client: httpx.AsyncClient,
    *,
    model_ref: ModelRef,
    user_prompt: str,
    timeout_seconds: float,
    system_prompt: str | None = None,
) -> tuple[dict[str, Any], int]:
    """Call judge LLM once; on parse contract failure, retry once with schema reminder."""

    def _is_parse_contract_error(exc: BaseException) -> bool:
        if isinstance(exc, JudgeParseError):
            return True
        return isinstance(exc, ValueError) and str(exc) == "judge_outcome_invalid"

    try:
        raw = await llm_dispatch.call_judge_llm(
            client,
            model_ref=model_ref,
            user_prompt=user_prompt,
            timeout_seconds=timeout_seconds,
            system_prompt=system_prompt,
        )
        anthropic_review.parse_judge_outcome(raw)
        return raw, 0
    except Exception as exc:
        if not _is_parse_contract_error(exc):
            raise
        parse_error = getattr(exc, "code", str(exc))
        retry_prompt = (
            f"{user_prompt}\n\n"
            f"Previous judge response failed parse ({parse_error}). "
            f"{_JUDGE_RETRY_SCHEMA_REMINDER}"
        )
        try:
            raw = await llm_dispatch.call_judge_llm(
                client,
                model_ref=model_ref,
                user_prompt=retry_prompt,
                timeout_seconds=timeout_seconds,
                system_prompt=system_prompt,
            )
            anthropic_review.parse_judge_outcome(raw)
            return raw, 1
        except Exception as retry_exc:
            if not _is_parse_contract_error(retry_exc):
                raise
            if (
                isinstance(exc, JudgeParseError)
                and isinstance(retry_exc, JudgeParseError)
                and exc.response_text
            ):
                retry_exc.response_text = exc.response_text
            retry_exc.judge_retry_count = 1
            raise


def _judge_failure_log_extra(group_id: UUID, exc: Exception) -> dict[str, object]:
    raw_response_text, parse_error, response_chars = judge_failure_trace_fields(exc)
    transport = anthropic_review.get_judge_transport_log_fields()
    merged_error = transport.get("parse_error") or parse_error
    if merged_error is None and isinstance(exc, httpx.HTTPError):
        merged_error = str(exc) or type(exc).__name__
    extra: dict[str, object] = {
        "group_id": str(group_id),
        "error": merged_error,
    }
    extra.update(transport)
    extra["error"] = extra.get("parse_error") or extra.get("error") or merged_error
    if response_chars is not None:
        extra["response_chars"] = response_chars
    preview = raw_response_text or transport.get("response_body_preview")
    if isinstance(preview, str) and preview:
        extra["parse_error"] = extra.get("parse_error") or parse_error or extra.get("error")
        extra["raw_response_text"] = preview
    return extra


def _judge_failure_artifact(
    *,
    group_id: UUID,
    evidence_snippet: str | None,
    user_prompt: str,
    file_patch_chars: int | None,
    exc: Exception,
    retry_count: int = 0,
) -> JudgeCandidateArtifact:
    raw_response_text, parse_error, _ = judge_failure_trace_fields(exc)
    return JudgeCandidateArtifact(
        group_id=group_id,
        evidence_snippet=evidence_snippet,
        user_prompt=user_prompt,
        raw_response=None,
        raw_response_text=raw_response_text,
        parse_error=parse_error,
        outcome=None,
        file_patch_chars=file_patch_chars,
        lock_ids_cited=None,
        retry_count=retry_count,
    )


def is_judge_candidate(*, severity: FindingSeverity, category: FindingCategory) -> bool:
    if severity in (FindingSeverity.error, FindingSeverity.critical):
        return True
    return (
        category == FindingCategory.security
        and severity_rank(severity) >= severity_rank(FindingSeverity.warning)
    )


def judge_candidate_group_sql_predicate():
    """SQL mirror of is_judge_candidate for group row severity/category."""
    return or_(
        GitHubFindingGroupORM.severity.in_(
            (FindingSeverity.error, FindingSeverity.critical),
        ),
        and_(
            GitHubFindingGroupORM.category == FindingCategory.security,
            GitHubFindingGroupORM.severity.in_(
                (FindingSeverity.warning, FindingSeverity.error, FindingSeverity.critical),
            ),
        ),
    )


def _build_judge_prompt(
    *,
    group: GitHubFindingGroupORM,
    evidence_snippet: str | None,
    start_line: int | None = None,
    end_line: int | None = None,
    suggestion: str | None = None,
    file_patch: str | None = None,
    engineering_block: str | None = None,
) -> str:
    parts = [
        "Automated reviewer (Moonshot) raised the finding below. Verify this claim only.",
        "Do not introduce new findings.",
        "",
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
    if evidence_snippet and evidence_snippet.strip():
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
    if engineering_block:
        parts.extend(
            [
                "",
                "Engineering context (authoritative locks):",
                engineering_block,
            ]
        )
    prompt_patch = resolve_judge_prompt_file_patch(evidence_snippet, file_patch)
    if prompt_patch:
        parts.extend(
            [
                "",
                "File diff (scoped):",
                prompt_patch,
            ]
        )
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
    patches_by_file: dict[str, str],
    engineering_pack: EngineeringContextPack | None = None,
    artifacts_out: list[JudgeCandidateArtifact] | None = None,
) -> int:
    judged = 0
    engineering_block = format_judge_engineering_context(engineering_pack)
    lock_ids_cited = list(engineering_pack.lock_ids) if engineering_pack and engineering_pack.lock_ids else None
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

            code_context = resolve_judge_code_context(
                file_path=finding.file_path,
                start_line=finding.start_line,
                patches_by_file=patches_by_file,
                supplemental_top_by_file={},
            )
            evidence_snippet = finding.evidence_snippet or code_context.evidence_snippet
            file_patch = code_context.file_patch
            patch_chars = judge_prompt_file_patch_chars(evidence_snippet, file_patch)
            user_prompt = _build_judge_prompt(
                group=group,
                evidence_snippet=evidence_snippet,
                start_line=finding.start_line,
                end_line=finding.end_line,
                suggestion=finding.suggestion,
                file_patch=file_patch,
                engineering_block=engineering_block,
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
                )
                outcome_str, notes = anthropic_review.parse_judge_outcome(raw)
            except (httpx.HTTPError, ValueError, ServiceUnavailableError) as exc:
                logger.error(
                    "github_finding_judge_failed",
                    extra=_judge_failure_log_extra(group.id, exc),
                )
                if artifacts_out is not None:
                    artifacts_out.append(
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
                    judge_provider=model_ref.provider,
                    judge_model_id=model_ref.model_id,
                    judge_notes=notes,
                )
            )

            if outcome == GitHubJudgeOutcome.dismissed:
                dismiss_fields = apply_resolution_method_on_judge_dismiss(
                    outcome=outcome,
                    resolved_at_revision_id=run.revision_id,
                )
                if dismiss_fields is not None:
                    for key, value in dismiss_fields.items():
                        setattr(group, key, value)
            elif outcome == GitHubJudgeOutcome.modified:
                group.severity = FindingSeverity.warning

            if artifacts_out is not None:
                input_tokens, output_tokens = anthropic_review.judge_token_usage_from_transport()
                artifacts_out.append(
                    JudgeCandidateArtifact(
                        group_id=group.id,
                        evidence_snippet=evidence_snippet,
                        user_prompt=user_prompt,
                        raw_response=anthropic_review.judge_raw_response_with_usage(raw),
                        outcome=outcome_str,
                        file_patch_chars=patch_chars,
                        lock_ids_cited=lock_ids_cited,
                        retry_count=retry_count,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
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
) -> tuple[int, ModelRef | None]:
    """Count escalation candidates, persist judge status, run judge when applicable."""
    run, candidates = await _load_judge_candidates(session, review_run_id=review_run_id)
    if run is None:
        return 0, None

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
        return 0, None

    if not settings.judge_llm_enabled():
        if await _review_run_has_judge_outcomes(session, review_run_id=review_run_id):
            run.judge_status = GitHubReviewJudgeStatus.completed
        else:
            run.judge_status = GitHubReviewJudgeStatus.skipped_disabled
        await session.flush()
        return 0, None

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
        return 0, None

    revision = await session.get(GitHubPullRequestRevisionORM, run.revision_id)
    engineering_pack = EngineeringContextPack()
    patches_by_file: dict[str, str] = {}
    if revision is not None:
        pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
        if pull_request is not None:
            async with httpx.AsyncClient(timeout=120.0) as client:
                compare_ctx = await fetch_compare_review_context(
                    session,
                    pull_request=pull_request,
                    revision=revision,
                    client=client,
                )
                patches_by_file = compare_ctx.patches_by_file
                if (
                    compare_ctx.github_installation_id is not None
                    and compare_ctx.owner is not None
                    and compare_ctx.repo_name is not None
                ):
                    engineering_pack = await build_engineering_context_pack(
                        client,
                        github_installation_id=compare_ctx.github_installation_id,
                        owner=compare_ctx.owner,
                        repo=compare_ctx.repo_name,
                        head_sha=revision.head_sha,
                        changed_files=frozenset(compare_ctx.changed_files),
                        omitted_files=frozenset(compare_ctx.omitted_files),
                        patches_by_file=patches_by_file,
                    )

    judged = await _run_judge_llm_loop(
        session,
        run=run,
        review_run_id=review_run_id,
        candidates=candidates,
        model_ref=model_ref,
        patches_by_file=patches_by_file,
        engineering_pack=engineering_pack,
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
    return judged, model_ref


async def finalize_review_run_judge_status(
    session: AsyncSession,
    *,
    review_run_id: UUID,
) -> None:
    """Re-evaluate judge_status after verification judge (JT-SP5).

    Verification may persist outcomes for escalation groups that discovery judge
    failed to reach; publish gating uses any-purpose outcomes per group.
    """
    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None or run.judge_status != GitHubReviewJudgeStatus.skipped_unavailable:
        return
    _run, candidates = await _load_judge_candidates(session, review_run_id=review_run_id)
    if _run is None:
        return
    if not await _judge_candidates_missing_outcome(
        session,
        review_run_id=review_run_id,
        candidates=candidates,
    ):
        run.judge_status = GitHubReviewJudgeStatus.completed
        await session.flush()


async def run_judge_for_review_run(
    session: AsyncSession, *, review_run_id: UUID
) -> tuple[int, ModelRef | None]:
    """Run judge on escalation candidates. Returns outcome count and model ref when judged."""
    return await record_review_run_judge_status(session, review_run_id=review_run_id)
