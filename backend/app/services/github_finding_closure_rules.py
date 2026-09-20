# backend/app/services/github_finding_closure_rules.py
"""Pure finding-group closure rules — no judge/reconcile imports."""
from __future__ import annotations

from uuid import UUID

from app.constants.enums import (
    GitHubFindingGroupState,
    GitHubJudgeOutcome,
    ResolutionMethod,
)

COMPARE_FAILED_REASON = "compare_failed"
HEAD_CHECK_FAILED_REASON = "head_check_failed"


def should_close_absent_and_addressed(
    *,
    state: GitHubFindingGroupState,
    bound_this_run: bool,
    this_run_finding_count: int,
    path_gone: bool,
    closure_blocked_reason: str | None,
) -> bool:
    """H2: close active unbound group when path gone or zero findings remain in file+category.

    P1 replaces the old ``addressed`` requirement with a count-based gate:
    close iff not bound this run AND (path_gone or this_run_finding_count == 0).
    ``this_run_finding_count >= 1`` (leftovers still reported) → stay open.
    """
    if state != GitHubFindingGroupState.active:
        return False
    if bound_this_run:
        return False
    if not (path_gone or this_run_finding_count == 0):
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


def apply_resolution_method_on_human_dismiss(
    *,
    resolved_at_revision_id: UUID,
) -> dict[str, object]:
    return {
        "state": GitHubFindingGroupState.resolved,
        "resolution_method": ResolutionMethod.human_dismissed,
        "resolved_at_revision_id": resolved_at_revision_id,
        "closure_blocked_reason": None,
    }


def should_reopen_absent_and_addressed(
    *,
    state: GitHubFindingGroupState,
    resolution_method: ResolutionMethod | None,
    bound_this_run: bool,
) -> bool:
    """FR-Q13: re-raise resolved group that is bound again (same identity reappeared after H2 closure)."""
    if state != GitHubFindingGroupState.resolved:
        return False
    if resolution_method != ResolutionMethod.absent_and_addressed:
        return False
    return bound_this_run


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
