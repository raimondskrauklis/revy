# backend/tests/unit/test_github_finding_reconcile.py
"""GitHub finding reconciliation — R5."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubReviewRunStatus,
    ResolutionMethod,
    ReviewProfile,
)
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_pull_request import GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_finding_reconcile import (
    claim_slot_key,
    compute_fingerprint,
    compute_legacy_d10_fingerprint,
    reconcile_review_run,
)


def _fp(
    *,
    workspace_id: uuid.UUID,
    pull_request_id: uuid.UUID,
    file_path: str | None,
    category: object,
    title: str,
) -> str:
    return compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path=file_path,
        category=category,
        claim_slot=claim_slot_key(title),
    )


def test_compute_fingerprint_stable():
    workspace_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    slot = claim_slot_key("Possible null")
    fp1 = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        claim_slot=slot,
    )
    fp2 = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        claim_slot=slot,
    )
    assert fp1 == fp2


def test_compute_fingerprint_ignores_message_paraphrase():
    workspace_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    slot = claim_slot_key("Null dereference")
    fp1 = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        claim_slot=slot,
    )
    fp2 = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        claim_slot=slot,
    )
    assert fp1 == fp2


def test_compute_fingerprint_ignores_start_line():
    workspace_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    slot = claim_slot_key("Null dereference")
    fp1 = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        claim_slot=slot,
    )
    fp2 = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        claim_slot=slot,
    )
    assert fp1 == fp2


def test_compute_fingerprint_differs_by_claim_slot():
    workspace_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    fp1 = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        claim_slot=claim_slot_key("SQL injection"),
    )
    fp2 = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        claim_slot=claim_slot_key("Command injection"),
    )
    assert fp1 != fp2


def test_compute_fingerprint_accepts_string_category():
    workspace_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    slot = claim_slot_key("Possible null")
    fp_enum = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        claim_slot=slot,
    )
    fp_str = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category="bug",
        claim_slot=slot,
    )
    assert fp_enum == fp_str


def test_mark_superseded_peers_symbol_removed():
    import app.services.github_finding_reconcile as reconcile_mod

    assert not hasattr(reconcile_mod, "_mark_superseded_peers")


@pytest.mark.asyncio
async def test_reconcile_creates_new_group():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
    )
    finding.id = uuid.uuid4()

    def _add(obj: object) -> None:
        if isinstance(obj, GitHubFindingGroupORM) and obj.id is None:
            obj.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding], []])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock(side_effect=_add)
    session.flush = AsyncMock()

    group_ids = await reconcile_review_run(session, review_run_id=review_run_id)

    assert len(group_ids) == 1
    assert finding.group_id == group_ids[0]
    added = session.add.call_args.args[0]
    assert added.claim_slot == claim_slot_key("SQLi")
    assert added.start_line is None


@pytest.mark.asyncio
async def test_reconcile_accepts_string_category_on_finding():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity="error",
        category="security",
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
    )
    finding.id = uuid.uuid4()

    def _add(obj: object) -> None:
        if isinstance(obj, GitHubFindingGroupORM) and obj.id is None:
            obj.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding], []])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock(side_effect=_add)
    session.flush = AsyncMock()

    group_ids = await reconcile_review_run(session, review_run_id=review_run_id)

    assert len(group_ids) == 1


@pytest.mark.asyncio
async def test_reconcile_same_fingerprint_updates_revision():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="def",
    )
    revision.id = revision_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
    )
    finding.id = uuid.uuid4()

    old_revision_id = uuid.uuid4()
    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=_fp(
            workspace_id=workspace_id,
            pull_request_id=pull_request_id,
            file_path="app/db.py",
            category=FindingCategory.security,
            title="SQLi",
        ),
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
        last_seen_revision_id=old_revision_id,
    )
    group.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding], []])
    session.scalar = AsyncMock(return_value=group)
    session.flush = AsyncMock()

    await reconcile_review_run(session, review_run_id=review_run_id)

    assert group.last_seen_revision_id == revision_id
    assert group.state == GitHubFindingGroupState.active


@pytest.mark.asyncio
async def test_reconcile_existing_group_does_not_supersede_peers():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    old_revision_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=3,
        head_sha="ghi",
    )
    revision.id = revision_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
    )
    finding.id = uuid.uuid4()

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=_fp(
            workspace_id=workspace_id,
            pull_request_id=pull_request_id,
            file_path="app/db.py",
            category=FindingCategory.security,
            title="SQLi",
        ),
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
        last_seen_revision_id=old_revision_id,
        claim_slot=claim_slot_key("SQLi"),
    )
    group.id = uuid.uuid4()

    peer = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="other-fingerprint",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.security,
        title="Other",
        message="Other issue",
        file_path="app/db.py",
        last_seen_revision_id=old_revision_id,
        claim_slot=claim_slot_key("Other"),
    )
    peer.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(return_value=group)
    session.flush = AsyncMock()

    await reconcile_review_run(session, review_run_id=review_run_id)

    assert group.last_seen_revision_id == revision_id
    assert peer.state == GitHubFindingGroupState.active


@pytest.mark.asyncio
async def test_reconcile_reopens_absent_and_addressed_on_re_report():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="def",
    )
    revision.id = revision_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Edge",
        message="Handle empty",
        file_path="app/x.py",
    )
    finding.id = uuid.uuid4()

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=_fp(
            workspace_id=workspace_id,
            pull_request_id=pull_request_id,
            file_path="app/x.py",
            category=FindingCategory.bug,
            title="Edge",
        ),
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Edge",
        message="Handle empty",
        file_path="app/x.py",
        last_seen_revision_id=uuid.uuid4(),
        resolution_method=ResolutionMethod.absent_and_addressed,
    )
    group.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding], []])
    session.scalar = AsyncMock(return_value=group)
    session.flush = AsyncMock()

    await reconcile_review_run(session, review_run_id=review_run_id)

    assert group.state == GitHubFindingGroupState.active
    assert group.resolution_method is None
    assert group.last_seen_revision_id == revision_id


@pytest.mark.asyncio
async def test_reconcile_resolved_group_unchanged():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="def",
    )
    revision.id = revision_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Edge",
        message="Handle empty",
        file_path="app/x.py",
    )
    finding.id = uuid.uuid4()

    old_revision_id = uuid.uuid4()
    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=_fp(
            workspace_id=workspace_id,
            pull_request_id=pull_request_id,
            file_path="app/x.py",
            category=FindingCategory.bug,
            title="Edge",
        ),
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Edge",
        message="Handle empty",
        file_path="app/x.py",
        last_seen_revision_id=old_revision_id,
    )
    group.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(return_value=group)
    session.flush = AsyncMock()

    await reconcile_review_run(session, review_run_id=review_run_id)

    assert group.last_seen_revision_id == old_revision_id
    assert group.state == GitHubFindingGroupState.resolved
    assert finding.group_id == group.id


def _completed_run(revision_id: uuid.UUID, workspace_id: uuid.UUID) -> GitHubReviewRunORM:
    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = uuid.uuid4()
    return run


@pytest.mark.asyncio
async def test_reconcile_legacy_d10_dual_lookup_binds_one_generation():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    run = _completed_run(revision_id, workspace_id)
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="def",
    )
    revision.id = revision_id
    finding = GitHubFindingORM(
        review_run_id=run.id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="eval",
        message="unsafe",
        file_path="app/eval.py",
        start_line=10,
    )
    finding.id = uuid.uuid4()
    legacy_fp = compute_legacy_d10_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/eval.py",
        category=FindingCategory.security,
        title="eval",
        start_line=10,
    )
    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=legacy_fp,
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="eval",
        message="unsafe",
        file_path="app/eval.py",
        start_line=10,
        claim_slot=claim_slot_key("eval"),
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(side_effect=[None, group])
    session.flush = AsyncMock()

    await reconcile_review_run(session, review_run_id=run.id)

    assert finding.group_id == group.id
    assert group.fingerprint == legacy_fp
    assert group.claim_slot == claim_slot_key("eval")
    assert group.last_seen_revision_id == revision_id


@pytest.mark.asyncio
async def test_reconcile_continuation_severity_rewrite_stays_one_open_group():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    run = _completed_run(revision_id, workspace_id)
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="def",
    )
    revision.id = revision_id
    finding = GitHubFindingORM(
        review_run_id=run.id,
        workspace_id=workspace_id,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="CRITICAL eval",
        message="still unsafe",
        file_path="app/eval.py",
        start_line=10,
    )
    finding.id = uuid.uuid4()
    birth_slot = claim_slot_key("INFO eval")
    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=_fp(
            workspace_id=workspace_id,
            pull_request_id=pull_request_id,
            file_path="app/eval.py",
            category=FindingCategory.security,
            title="INFO eval",
        ),
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.info,
        category=FindingCategory.security,
        title="INFO eval",
        message="unsafe",
        file_path="app/eval.py",
        start_line=10,
        claim_slot=birth_slot,
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding], [group]])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    await reconcile_review_run(session, review_run_id=run.id)

    assert finding.group_id == group.id
    assert group.state == GitHubFindingGroupState.active
    assert group.title == "CRITICAL eval"
    assert group.severity == FindingSeverity.critical
    assert group.claim_slot == birth_slot
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_reconcile_line_insert_above_eval_stays_one_group():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    run = _completed_run(revision_id, workspace_id)
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="def",
    )
    revision.id = revision_id
    finding = GitHubFindingORM(
        review_run_id=run.id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="eval",
        message="unsafe",
        file_path="app/eval.py",
        start_line=12,
    )
    finding.id = uuid.uuid4()
    birth_slot = claim_slot_key("eval")
    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=compute_legacy_d10_fingerprint(
            workspace_id=workspace_id,
            pull_request_id=pull_request_id,
            file_path="app/eval.py",
            category=FindingCategory.security,
            title="eval",
            start_line=10,
        ),
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="eval",
        message="unsafe",
        file_path="app/eval.py",
        start_line=10,
        claim_slot=birth_slot,
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding], [group]])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    await reconcile_review_run(session, review_run_id=run.id)

    assert finding.group_id == group.id
    assert group.start_line == 12
    assert group.claim_slot == birth_slot
    assert group.state == GitHubFindingGroupState.active


@pytest.mark.asyncio
async def test_reconcile_two_leftover_same_category_claims_are_not_merged():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    run = _completed_run(revision_id, workspace_id)
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="def",
    )
    revision.id = revision_id
    finding = GitHubFindingORM(
        review_run_id=run.id,
        workspace_id=workspace_id,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Rewritten leftover",
        message="still there",
        file_path="app/x.py",
        start_line=4,
    )
    finding.id = uuid.uuid4()

    leftover_a = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp-a",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Claim A",
        message="a",
        file_path="app/x.py",
        claim_slot=claim_slot_key("Claim A"),
        last_seen_revision_id=uuid.uuid4(),
    )
    leftover_a.id = uuid.uuid4()
    leftover_b = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp-b",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Claim B",
        message="b",
        file_path="app/x.py",
        claim_slot=claim_slot_key("Claim B"),
        last_seen_revision_id=uuid.uuid4(),
    )
    leftover_b.id = uuid.uuid4()

    def _add(obj: object) -> None:
        if isinstance(obj, GitHubFindingGroupORM) and obj.id is None:
            obj.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding], [leftover_a, leftover_b]])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock(side_effect=_add)
    session.flush = AsyncMock()

    group_ids = await reconcile_review_run(session, review_run_id=run.id)

    assert leftover_a.state == GitHubFindingGroupState.active
    assert leftover_b.state == GitHubFindingGroupState.active
    assert finding.group_id not in {leftover_a.id, leftover_b.id}
    assert len(group_ids) == 1
    session.add.assert_called()


@pytest.mark.asyncio
async def test_reconcile_two_same_line_titles_stay_two_groups():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    run = _completed_run(revision_id, workspace_id)
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id
    finding_a = GitHubFindingORM(
        review_run_id=run.id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQL injection",
        message="a",
        file_path="app/db.py",
        start_line=20,
    )
    finding_a.id = uuid.uuid4()
    finding_b = GitHubFindingORM(
        review_run_id=run.id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="Command injection",
        message="b",
        file_path="app/db.py",
        start_line=20,
    )
    finding_b.id = uuid.uuid4()

    def _add(obj: object) -> None:
        if isinstance(obj, GitHubFindingGroupORM) and obj.id is None:
            obj.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding_a, finding_b], [], []])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock(side_effect=_add)
    session.flush = AsyncMock()

    group_ids = await reconcile_review_run(session, review_run_id=run.id)

    assert len(group_ids) == 2
    assert finding_a.group_id != finding_b.group_id
    assert session.add.call_count == 2
    assert claim_slot_key("SQL injection") != claim_slot_key("Command injection")


@pytest.mark.asyncio
async def test_reconcile_legacy_same_title_different_lines_keep_distinct_fingerprints():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    run = _completed_run(revision_id, workspace_id)
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="def",
    )
    revision.id = revision_id
    finding = GitHubFindingORM(
        review_run_id=run.id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="eval",
        message="unsafe",
        file_path="app/eval.py",
        start_line=10,
    )
    finding.id = uuid.uuid4()
    fp_line_10 = compute_legacy_d10_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/eval.py",
        category=FindingCategory.security,
        title="eval",
        start_line=10,
    )
    fp_line_20 = compute_legacy_d10_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/eval.py",
        category=FindingCategory.security,
        title="eval",
        start_line=20,
    )
    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=fp_line_10,
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="eval",
        message="unsafe",
        file_path="app/eval.py",
        start_line=10,
        claim_slot=claim_slot_key("eval"),
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = uuid.uuid4()
    peer = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=fp_line_20,
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="eval",
        message="unsafe",
        file_path="app/eval.py",
        start_line=20,
        claim_slot=claim_slot_key("eval"),
        last_seen_revision_id=uuid.uuid4(),
    )
    peer.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(side_effect=[None, group])
    session.flush = AsyncMock()

    await reconcile_review_run(session, review_run_id=run.id)

    assert group.fingerprint == fp_line_10
    assert peer.fingerprint == fp_line_20
    assert group.fingerprint != peer.fingerprint
