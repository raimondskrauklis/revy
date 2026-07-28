# backend/app/services/github_finding_closure.py
"""Finding group closure rules — pure functions for Pass 2+ (P0 contract)."""
from __future__ import annotations

from uuid import UUID

from app.constants.enums import (
    GitHubFindingGroupState,
    GitHubJudgeOutcome,
    ResolutionMethod,
    ResolutionStatus,
)

COMPARE_FAILED_REASON = "compare_failed"


def should_close_absent_and_addressed(
    *,
    fingerprint_in_current_run: bool,
    resolution_status: ResolutionStatus | None,
    closure_blocked_reason: str | None,
) -> bool:
    """FR-Q3: absent fingerprint + addressed on prior revision, compare succeeded."""
    if fingerprint_in_current_run:
        return False
    if resolution_status != ResolutionStatus.addressed:
        return False
    return closure_blocked_reason != COMPARE_FAILED_REASON


def closure_fields_for_absent_and_addressed(
    *,
    resolved_at_revision_id: UUID,
) -> dict[str, object]:
    return {
        "state": GitHubFindingGroupState.resolved,
        "resolution_method": ResolutionMethod.absent_and_addressed,
        "resolved_at_revision_id": resolved_at_revision_id,
    }


def apply_resolution_method_on_judge_dismiss(
    *,
    outcome: GitHubJudgeOutcome,
    resolved_at_revision_id: UUID,
) -> dict[str, object] | None:
    """Discovery judge dismiss → resolved + judge_dismissed (P1 wires this)."""
    if outcome != GitHubJudgeOutcome.dismissed:
        return None
    return {
        "state": GitHubFindingGroupState.resolved,
        "resolution_method": ResolutionMethod.judge_dismissed,
        "resolved_at_revision_id": resolved_at_revision_id,
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
    """Replace blind `elif resolved: pass` — only skip judge/human dismiss paths."""
    if state != GitHubFindingGroupState.resolved:
        return False
    return resolution_method in (
        ResolutionMethod.judge_dismissed,
        ResolutionMethod.verification_dismissed,
        ResolutionMethod.human_dismissed,
        None,
    )
