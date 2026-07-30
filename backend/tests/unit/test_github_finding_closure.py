# backend/tests/unit/test_github_finding_closure.py
"""Finding group closure rules — P0 pure functions."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubJudgeOutcome,
    GitHubReviewRunStatus,
    ResolutionMethod,
    ResolutionStatus,
)
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services import github_resolution_metrics
from app.services.github_finding_closure import (
    VERIFICATION_JUDGE_MAX_PER_RUN,
    apply_pass2_closure_for_review_run,
    is_verification_escalation_candidate,
    verify_still_open_escalation_groups,
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


@pytest.mark.asyncio
async def test_apply_pass2_closure_closes_absent_addressed_group():
    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    prior_revision_id = uuid.uuid4()
    current_revision_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        workspace_id=uuid.uuid4(),
        revision_id=current_revision_id,
        status=GitHubReviewRunStatus.completed,
    )
    run.id = review_run_id

    published_prior = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="published",
        base_sha="base",
    )
    published_prior.id = prior_revision_id

    current_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=3,
        head_sha="head",
        base_sha="base",
    )
    current_revision.id = current_revision_id

    group = GitHubFindingGroupORM(
        workspace_id=run.workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="absent-fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/a.py",
        last_seen_revision_id=prior_revision_id,
        resolution_status=ResolutionStatus.addressed,
    )

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, current_revision])
    session.scalars = AsyncMock(return_value=[group])
    session.flush = AsyncMock()

    with patch(
        "app.services.github_finding_closure.get_last_published_prior_revision",
        AsyncMock(return_value=published_prior),
    ):
        with patch(
            "app.services.github_finding_closure.get_intermediate_revision_ids_between",
            AsyncMock(return_value=frozenset()),
        ):
            with patch(
                "app.services.github_finding_closure._fingerprints_in_review_run",
                AsyncMock(return_value=set()),
            ):
                closed = await apply_pass2_closure_for_review_run(
                    session,
                    review_run_id=review_run_id,
                )

    assert closed == 1
    assert group.state == GitHubFindingGroupState.resolved
    assert group.resolution_method == ResolutionMethod.absent_and_addressed


@pytest.mark.asyncio
async def test_apply_pass2_closure_e2e_aged_group_outside_pairing():
    """E2E: aged group addressed by hygiene, closed via widened Pass 2 query."""
    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    rev1_id = uuid.uuid4()
    rev2_id = uuid.uuid4()
    rev3_id = uuid.uuid4()

    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state="open",
        head_sha="head3",
        head_ref="feature",
        base_ref="main",
        revision_count=3,
    )
    pull_request.id = pull_request_id

    published_prior = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="head2",
        base_sha="base",
    )
    published_prior.id = rev2_id

    current_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=3,
        head_sha="head3",
        base_sha="base",
    )
    current_revision.id = rev3_id

    aged_group = GitHubFindingGroupORM(
        workspace_id=pull_request.workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="aged-fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Aged",
        message="msg",
        file_path="backend/probe/deleted.py",
        last_seen_revision_id=rev1_id,
        resolution_status=ResolutionStatus.addressed,
    )

    run = GitHubReviewRunORM(
        workspace_id=pull_request.workspace_id,
        revision_id=rev3_id,
        status=GitHubReviewRunStatus.completed,
    )
    run.id = review_run_id

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, current_revision])
    session.scalars = AsyncMock(return_value=[aged_group])
    session.flush = AsyncMock()

    with patch(
        "app.services.github_finding_closure.get_last_published_prior_revision",
        AsyncMock(return_value=published_prior),
    ):
        with patch(
            "app.services.github_finding_closure.get_intermediate_revision_ids_between",
            AsyncMock(return_value=frozenset()),
        ):
            with patch(
                "app.services.github_finding_closure._fingerprints_in_review_run",
                AsyncMock(return_value=set()),
            ):
                closed = await apply_pass2_closure_for_review_run(
                    session,
                    review_run_id=review_run_id,
                )

    assert closed == 1
    assert aged_group.state == GitHubFindingGroupState.resolved
    assert aged_group.resolution_method == ResolutionMethod.absent_and_addressed


@pytest.mark.asyncio
async def test_apply_pass2_closure_after_file_deletion_pass1_stamp():
    """FR-DG2a: deletion push stamps addressed on sync, then Pass 2 closes absent fingerprint."""
    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    prior_revision_id = uuid.uuid4()
    current_revision_id = uuid.uuid4()

    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state="open",
        head_sha="head",
        head_ref="feature",
        base_ref="main",
        revision_count=2,
    )
    pull_request.id = pull_request_id

    published_prior = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="published",
        base_sha="base",
    )
    published_prior.id = prior_revision_id

    current_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="head",
        base_sha="base",
    )
    current_revision.id = current_revision_id

    group = GitHubFindingGroupORM(
        workspace_id=pull_request.workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="probe-fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Probe defect",
        message="msg",
        file_path="backend/tests/fixtures/fr_dogfood/probe_module.py",
        last_seen_revision_id=prior_revision_id,
    )

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[published_prior])
    session.scalars = AsyncMock(return_value=[group])
    session.flush = AsyncMock()

    with patch(
        "app.services.github_resolution_metrics._fetch_compare_patches",
        AsyncMock(
            return_value=type(
                "CompareResult",
                (),
                {
                    "patches_by_file": {},
                    "compare_failed": False,
                    "removed_paths": frozenset(
                        {"backend/tests/fixtures/fr_dogfood/probe_module.py"}
                    ),
                    "deleted_paths": frozenset(
                        {"backend/tests/fixtures/fr_dogfood/probe_module.py"}
                    ),
                    "renamed_from_paths": frozenset(),
                },
            )()
        ),
    ):
        with patch(
            "app.services.github_resolution_metrics.paths_absent_at_head",
            AsyncMock(
                return_value={
                    "backend/tests/fixtures/fr_dogfood/probe_module.py": True,
                }
            ),
        ):
            with patch(
                "app.services.github_resolution_metrics._latest_finding_lines",
                AsyncMock(return_value=(5, 5)),
            ):
                stamped = await github_resolution_metrics.apply_resolution_status_for_synchronize(
                    session,
                    pull_request=pull_request,
                    new_revision=current_revision,
                )

    assert stamped == 1
    assert group.resolution_status == ResolutionStatus.addressed

    run = GitHubReviewRunORM(
        workspace_id=pull_request.workspace_id,
        revision_id=current_revision_id,
        status=GitHubReviewRunStatus.completed,
    )
    run.id = review_run_id

    session.get = AsyncMock(side_effect=[run, current_revision])
    session.scalars = AsyncMock(return_value=[group])

    with patch(
        "app.services.github_finding_closure.get_last_published_prior_revision",
        AsyncMock(return_value=published_prior),
    ):
        with patch(
            "app.services.github_finding_closure.get_intermediate_revision_ids_between",
            AsyncMock(return_value=frozenset()),
        ):
            with patch(
                "app.services.github_finding_closure._fingerprints_in_review_run",
                AsyncMock(return_value=set()),
            ):
                closed = await apply_pass2_closure_for_review_run(
                    session,
                    review_run_id=review_run_id,
                )

    assert closed == 1
    assert group.state == GitHubFindingGroupState.resolved
    assert group.resolution_method == ResolutionMethod.absent_and_addressed


@pytest.mark.asyncio
async def test_verify_still_open_escalation_outside_pairing():
    """Pass 3 widen: aged still_open group outside pairing window is judged when LLM enabled."""
    from unittest.mock import MagicMock

    from app.services.github_compare_patches import ComparePatchesResult
    from app.services.model_policy import ModelRef

    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    rev1_id = uuid.uuid4()
    rev2_id = uuid.uuid4()
    rev3_id = uuid.uuid4()
    group_id = uuid.uuid4()

    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state="open",
        head_sha="head3",
        head_ref="feature",
        base_ref="main",
        revision_count=3,
    )
    pull_request.id = pull_request_id

    published_prior = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="head2",
        base_sha="base",
    )
    published_prior.id = rev2_id

    current_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=3,
        head_sha="head3",
        base_sha="base",
    )
    current_revision.id = rev3_id

    aged_group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="aged-still-open",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Aged still open",
        message="msg",
        file_path="backend/probe/stale.py",
        last_seen_revision_id=rev1_id,
        resolution_status=ResolutionStatus.still_open,
    )
    aged_group.id = group_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Aged still open",
        message="msg",
        file_path="backend/probe/stale.py",
        group_id=group_id,
        evidence_snippet="stale line",
    )

    run = GitHubReviewRunORM(
        workspace_id=workspace_id,
        revision_id=rev3_id,
        status=GitHubReviewRunStatus.completed,
    )
    run.id = review_run_id

    compare_result = ComparePatchesResult(patches_by_file={}, compare_failed=False)

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, current_revision, pull_request])
    session.scalars = AsyncMock(return_value=[aged_group])
    session.scalar = AsyncMock(side_effect=[None, finding])
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.github_finding_closure.settings") as mock_settings:
        mock_settings.judge_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with patch(
            "app.services.github_finding_closure.get_last_published_prior_revision",
            AsyncMock(return_value=published_prior),
        ):
            with patch(
                "app.services.github_finding_closure._fingerprints_in_review_run",
                AsyncMock(return_value=set()),
            ):
                with patch(
                    "app.services.github_compare_patches.fetch_compare_patches",
                    AsyncMock(return_value=compare_result),
                ):
                    with patch(
                        "app.services.github_finding_closure.resolve_model",
                        AsyncMock(return_value=ModelRef(provider="anthropic", model_id="claude-test")),
                    ):
                        with patch(
                            "app.services.github_finding_closure.call_judge_with_optional_retry",
                            AsyncMock(
                                return_value=(
                                    {"outcome": "dismissed", "notes": "structural fix"},
                                    0,
                                )
                            ),
                        ):
                            result = await verify_still_open_escalation_groups(
                                session,
                                review_run_id=review_run_id,
                            )

    assert result.judged_count == 1
    assert aged_group.state == GitHubFindingGroupState.resolved
    assert aged_group.resolution_method == ResolutionMethod.verification_dismissed

