# backend/tests/unit/test_github_generation_lifecycle.py
"""Generation lifecycle authority and supersede helpers — P0."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import GitHubPullRequestState, GitHubReviewRunStatus, ReviewProfile
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_generation_lifecycle import (
    is_authoritative_for_pull_request_head,
    is_review_run_superseded,
    mark_active_review_runs_superseded_for_revision,
    mark_review_runs_superseded_for_pull_request,
    supersede_active_generations_for_revision,
    supersede_stale_generations_for_new_revision,
)


def _pull_request(*, head_sha: str = "head-sha") -> GitHubPullRequestORM:
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=2,
        is_draft=False,
    )
    pull_request.id = uuid.uuid4()
    return pull_request


def _revision(
    pull_request: GitHubPullRequestORM,
    *,
    revision_number: int,
    head_sha: str,
) -> GitHubPullRequestRevisionORM:
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request.id,
        revision_number=revision_number,
        head_sha=head_sha,
    )
    revision.id = uuid.uuid4()
    return revision


def _review_run(
    revision: GitHubPullRequestRevisionORM,
    *,
    status: GitHubReviewRunStatus,
) -> GitHubReviewRunORM:
    run = GitHubReviewRunORM(
        revision_id=revision.id,
        workspace_id=uuid.uuid4(),
        status=status,
        profile=ReviewProfile.standard,
    )
    run.id = uuid.uuid4()
    return run


@pytest.mark.asyncio
async def test_is_authoritative_when_revision_matches_pr_head_sha():
    pull_request = _pull_request(head_sha="abc123")
    revision = _revision(pull_request, revision_number=2, head_sha="abc123")
    session = AsyncMock()
    session.get = AsyncMock(side_effect=[revision, pull_request])

    assert await is_authoritative_for_pull_request_head(session, revision_id=revision.id) is True


@pytest.mark.asyncio
async def test_is_not_authoritative_when_pr_head_advanced():
    pull_request = _pull_request(head_sha="new-sha")
    revision = _revision(pull_request, revision_number=1, head_sha="old-sha")
    session = AsyncMock()
    session.get = AsyncMock(side_effect=[revision, pull_request])

    assert await is_authoritative_for_pull_request_head(session, revision_id=revision.id) is False


@pytest.mark.asyncio
async def test_mark_review_runs_superseded_for_pull_request_older_revisions_only():
    pull_request = _pull_request()
    old_revision = _revision(pull_request, revision_number=1, head_sha="old")
    keep_revision = _revision(pull_request, revision_number=2, head_sha="new")

    pending_old = _review_run(old_revision, status=GitHubReviewRunStatus.pending)
    processing_old = _review_run(old_revision, status=GitHubReviewRunStatus.processing)
    completed_old = _review_run(old_revision, status=GitHubReviewRunStatus.completed)
    pending_keep = _review_run(keep_revision, status=GitHubReviewRunStatus.pending)

    session = AsyncMock()
    session.get = AsyncMock(return_value=keep_revision)
    session.scalars = AsyncMock(
        side_effect=[
            [old_revision.id],
            [pending_old, processing_old],
        ]
    )
    session.flush = AsyncMock()

    superseded_ids = await mark_review_runs_superseded_for_pull_request(
        session,
        pull_request_id=pull_request.id,
        keep_revision_id=keep_revision.id,
    )

    assert set(superseded_ids) == {pending_old.id, processing_old.id}
    assert pending_old.status == GitHubReviewRunStatus.superseded
    assert processing_old.status == GitHubReviewRunStatus.superseded
    assert completed_old.status == GitHubReviewRunStatus.completed
    assert pending_keep.status == GitHubReviewRunStatus.pending
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_active_review_runs_superseded_for_revision():
    pull_request = _pull_request()
    revision = _revision(pull_request, revision_number=1, head_sha="sha")
    pending = _review_run(revision, status=GitHubReviewRunStatus.pending)
    completed = _review_run(revision, status=GitHubReviewRunStatus.completed)

    session = AsyncMock()
    session.get = AsyncMock(return_value=revision)
    session.scalars = AsyncMock(return_value=[pending])
    session.flush = AsyncMock()

    superseded_ids = await mark_active_review_runs_superseded_for_revision(
        session,
        revision_id=revision.id,
    )

    assert superseded_ids == [pending.id]
    assert pending.status == GitHubReviewRunStatus.superseded
    assert completed.status == GitHubReviewRunStatus.completed
    session.flush.assert_awaited_once()


def test_is_review_run_superseded():
    run = _review_run(
        _revision(_pull_request(), revision_number=1, head_sha="sha"),
        status=GitHubReviewRunStatus.superseded,
    )
    assert is_review_run_superseded(run) is True

    active = _review_run(
        _revision(_pull_request(), revision_number=1, head_sha="sha"),
        status=GitHubReviewRunStatus.pending,
    )
    assert is_review_run_superseded(active) is False


@pytest.mark.asyncio
async def test_supersede_stale_generations_for_new_revision_finalizes_pipelines():
    pull_request = _pull_request()
    old_revision = _revision(pull_request, revision_number=1, head_sha="old")
    keep_revision = _revision(pull_request, revision_number=2, head_sha="new")
    pending_old = _review_run(old_revision, status=GitHubReviewRunStatus.pending)
    pipeline_run_id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(return_value=keep_revision)
    session.scalars = AsyncMock(side_effect=[[old_revision.id], [pending_old]])
    session.flush = AsyncMock()

    pipeline_run = MagicMock()
    pipeline_run.id = pipeline_run_id

    with patch(
        "app.services.github_generation_lifecycle.get_pipeline_run_for_review_run",
        AsyncMock(return_value=pipeline_run),
    ):
        with patch(
            "app.services.github_generation_lifecycle.finalize_pipeline_github_check_neutral",
            AsyncMock(),
        ) as finalize_mock:
            superseded_ids = await supersede_stale_generations_for_new_revision(
                session,
                pull_request_id=pull_request.id,
                keep_revision_id=keep_revision.id,
            )

    assert superseded_ids == [pending_old.id]
    finalize_mock.assert_awaited_once_with(
        session,
        pipeline_run_id=pipeline_run_id,
        summary="Superseded by newer commit",
    )


@pytest.mark.asyncio
async def test_supersede_on_synchronize_hook_marks_older_runs_only():
    """P2.6 scenario: supersede helper only targets older revision runs."""
    pull_request = _pull_request(head_sha="h2-sha")
    h1_revision = _revision(pull_request, revision_number=1, head_sha="h1-sha")
    h2_revision = _revision(pull_request, revision_number=2, head_sha="h2-sha")
    h1_run = _review_run(h1_revision, status=GitHubReviewRunStatus.processing)

    session = AsyncMock()
    session.get = AsyncMock(return_value=h2_revision)
    session.scalars = AsyncMock(side_effect=[[h1_revision.id], [h1_run]])
    session.flush = AsyncMock()

    with patch(
        "app.services.github_generation_lifecycle.finalize_pipeline_checks_for_superseded_review_runs",
        AsyncMock(),
    ):
        superseded_ids = await supersede_stale_generations_for_new_revision(
            session,
            pull_request_id=pull_request.id,
            keep_revision_id=h2_revision.id,
        )

    assert superseded_ids == [h1_run.id]
    assert h1_run.status == GitHubReviewRunStatus.superseded


@pytest.mark.asyncio
async def test_supersede_active_generations_for_revision_finalizes_pipelines():
    pull_request = _pull_request()
    revision = _revision(pull_request, revision_number=1, head_sha="sha")
    pending = _review_run(revision, status=GitHubReviewRunStatus.pending)
    pipeline_run_id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(return_value=revision)
    session.scalars = AsyncMock(return_value=[pending])
    session.flush = AsyncMock()

    pipeline_run = MagicMock()
    pipeline_run.id = pipeline_run_id

    with patch(
        "app.services.github_generation_lifecycle.get_pipeline_run_for_review_run",
        AsyncMock(return_value=pipeline_run),
    ):
        with patch(
            "app.services.github_generation_lifecycle.finalize_pipeline_github_check_neutral",
            AsyncMock(),
        ) as finalize_mock:
            superseded_ids = await supersede_active_generations_for_revision(
                session,
                revision_id=revision.id,
            )

    assert superseded_ids == [pending.id]
    finalize_mock.assert_awaited_once()
