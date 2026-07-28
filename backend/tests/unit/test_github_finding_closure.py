# backend/tests/unit/test_github_finding_closure.py
"""Finding group closure rules — P0 pure functions."""
import uuid

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubJudgeOutcome,
    ResolutionMethod,
    ResolutionStatus,
)
from app.models.github_finding_group import GitHubFindingGroupORM
from app.services.github_finding_closure import (
    VERIFICATION_JUDGE_MAX_PER_RUN,
    is_verification_escalation_candidate,
)
from app.services.github_finding_closure_rules import (
    COMPARE_FAILED_REASON,
    apply_resolution_method_on_judge_dismiss,
    closure_fields_for_absent_and_addressed,
    reopen_fields_for_re_report,
    should_close_absent_and_addressed,
    should_reopen_absent_and_addressed,
    should_skip_resolved_group_on_reconcile,
)


def test_should_close_absent_and_addressed_when_addressed_and_absent():
    assert should_close_absent_and_addressed(
        state=GitHubFindingGroupState.active,
        fingerprint_in_current_run=False,
        resolution_status=ResolutionStatus.addressed,
        closure_blocked_reason=None,
    )


def test_should_not_close_when_group_already_resolved():
    assert not should_close_absent_and_addressed(
        state=GitHubFindingGroupState.resolved,
        fingerprint_in_current_run=False,
        resolution_status=ResolutionStatus.addressed,
        closure_blocked_reason=None,
    )


def test_should_not_close_when_fingerprint_in_run():
    assert not should_close_absent_and_addressed(
        state=GitHubFindingGroupState.active,
        fingerprint_in_current_run=True,
        resolution_status=ResolutionStatus.addressed,
        closure_blocked_reason=None,
    )


def test_should_not_close_when_compare_failed():
    assert not should_close_absent_and_addressed(
        state=GitHubFindingGroupState.active,
        fingerprint_in_current_run=False,
        resolution_status=ResolutionStatus.addressed,
        closure_blocked_reason=COMPARE_FAILED_REASON,
    )


def test_closure_fields_for_absent_and_addressed():
    revision_id = uuid.uuid4()
    fields = closure_fields_for_absent_and_addressed(resolved_at_revision_id=revision_id)
    assert fields["state"] == GitHubFindingGroupState.resolved
    assert fields["resolution_method"] == ResolutionMethod.absent_and_addressed
    assert fields["resolved_at_revision_id"] == revision_id
    assert fields["closure_blocked_reason"] is None


def test_should_not_close_when_other_block_reason():
    assert not should_close_absent_and_addressed(
        state=GitHubFindingGroupState.active,
        fingerprint_in_current_run=False,
        resolution_status=ResolutionStatus.addressed,
        closure_blocked_reason="judge_failed",
    )


def test_closure_fields_clear_blocked_reason():
    revision_id = uuid.uuid4()
    fields = closure_fields_for_absent_and_addressed(resolved_at_revision_id=revision_id)
    assert fields["closure_blocked_reason"] is None


def test_judge_dismiss_fields_clear_blocked_reason():
    revision_id = uuid.uuid4()
    fields = apply_resolution_method_on_judge_dismiss(
        outcome=GitHubJudgeOutcome.dismissed,
        resolved_at_revision_id=revision_id,
    )
    assert fields is not None
    assert fields["closure_blocked_reason"] is None


def test_apply_resolution_method_on_judge_dismiss():
    revision_id = uuid.uuid4()
    fields = apply_resolution_method_on_judge_dismiss(
        outcome=GitHubJudgeOutcome.dismissed,
        resolved_at_revision_id=revision_id,
    )
    assert fields is not None
    assert fields["resolution_method"] == ResolutionMethod.judge_dismissed


def test_apply_resolution_method_on_judge_dismiss_ignores_upheld():
    assert (
        apply_resolution_method_on_judge_dismiss(
            outcome=GitHubJudgeOutcome.upheld,
            resolved_at_revision_id=uuid.uuid4(),
        )
        is None
    )


def test_should_reopen_absent_and_addressed_on_re_report():
    assert should_reopen_absent_and_addressed(
        state=GitHubFindingGroupState.resolved,
        resolution_method=ResolutionMethod.absent_and_addressed,
        fingerprint_in_current_run=True,
    )


def test_should_not_reopen_when_group_active():
    assert not should_reopen_absent_and_addressed(
        state=GitHubFindingGroupState.active,
        resolution_method=ResolutionMethod.absent_and_addressed,
        fingerprint_in_current_run=True,
    )


def test_should_not_reopen_judge_dismissed():
    assert not should_reopen_absent_and_addressed(
        state=GitHubFindingGroupState.resolved,
        resolution_method=ResolutionMethod.judge_dismissed,
        fingerprint_in_current_run=True,
    )


def test_reopen_fields_clears_closure():
    fields = reopen_fields_for_re_report()
    assert fields["state"] == GitHubFindingGroupState.active
    assert fields["resolution_method"] is None
    assert fields["resolved_at_revision_id"] is None
    assert fields["closure_blocked_reason"] is None


def test_should_skip_resolved_judge_dismissed():
    assert should_skip_resolved_group_on_reconcile(
        state=GitHubFindingGroupState.resolved,
        resolution_method=ResolutionMethod.judge_dismissed,
    )


def test_should_not_skip_resolved_absent_and_addressed_for_reopen():
    assert not should_skip_resolved_group_on_reconcile(
        state=GitHubFindingGroupState.resolved,
        resolution_method=ResolutionMethod.absent_and_addressed,
    )


def test_verification_escalation_candidate_still_open_error():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/a.py",
        last_seen_revision_id=uuid.uuid4(),
        resolution_status=ResolutionStatus.still_open,
    )
    assert is_verification_escalation_candidate(group=group)


def test_verification_escalation_candidate_skips_compare_failed():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/a.py",
        last_seen_revision_id=uuid.uuid4(),
        resolution_status=ResolutionStatus.still_open,
        closure_blocked_reason=COMPARE_FAILED_REASON,
    )
    assert not is_verification_escalation_candidate(group=group)


def test_verification_judge_max_per_run_is_five():
    assert VERIFICATION_JUDGE_MAX_PER_RUN == 5
