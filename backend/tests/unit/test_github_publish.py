# backend/tests/unit/test_github_publish.py
"""GitHub publish service — R6."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubAccountType,
    GitHubFindingGroupState,
    GitHubPublishJobStatus,
    GitHubPullRequestState,
    GitHubRepositoryStatus,
    GitHubReviewRunStatus,
    ReviewProfile,
)
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_installation import GitHubInstallationORM
from app.models.github_publish_job import GitHubPublishJobORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services import github_publish
from app.services.github_publish import PublishJobRetryableError


def test_compute_check_conclusion_failure_on_critical():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="x",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="bad",
        file_path="a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    assert github_publish.compute_check_conclusion([group]) == "failure"


def test_compute_check_conclusion_neutral_on_warnings_only():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="x",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Edge",
        message="note",
        file_path="a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    assert github_publish.compute_check_conclusion([group]) == "neutral"


def test_build_summary_markdown_counts_active_findings_only():
    pull_request_id = uuid.uuid4()
    active = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="a",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="One",
        message="m",
        file_path="a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    superseded = GitHubFindingGroupORM(
        workspace_id=active.workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="b",
        state=GitHubFindingGroupState.superseded,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Old",
        message="m",
        file_path="b.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    markdown = github_publish.build_summary_markdown(
        pull_request_id=pull_request_id,
        groups=[active, superseded],
    )
    assert "of 1 findings" not in markdown
    assert "Old" not in markdown


def test_build_summary_markdown_escapes_pipe_in_cells():
    pull_request_id = uuid.uuid4()
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="pipe",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Bad | title",
        message="m",
        file_path="src/a|b.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    markdown = github_publish.build_summary_markdown(
        pull_request_id=pull_request_id,
        groups=[group],
    )
    assert "Bad \\| title" in markdown
    assert "src/a\\|b.py" in markdown
    assert "| Bad | title |" not in markdown


def test_inline_publish_findings_statement_filters_active_groups():
    review_run_id = uuid.uuid4()
    stmt = github_publish.inline_publish_findings_statement(review_run_id=review_run_id)
    sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "github_finding_groups" in sql
    assert GitHubFindingGroupState.active.value in sql


def test_compute_check_conclusion_success_when_no_active():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="x",
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Old",
        message="fixed",
        file_path="a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    assert github_publish.compute_check_conclusion([group]) == "success"


@pytest.mark.asyncio
async def test_run_publish_job_creates_check_run():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation]
    )
    session.scalars = AsyncMock(return_value=[])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    with patch("app.services.github_publish.github_api.create_check_run", AsyncMock(return_value=100)):
        with patch("app.services.github_publish.github_api.create_issue_comment", AsyncMock(return_value=200)):
            result = await github_publish.run_publish_job(session, publish_job_id=publish_job_id)

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_check_run_id == 100
    assert result.github_comment_id == 200


@pytest.mark.asyncio
async def test_run_publish_job_updates_existing_sha():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
    )
    job.id = publish_job_id

    existing = GitHubPublishJobORM(
        review_run_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.completed,
        github_check_run_id=50,
        github_comment_id=60,
    )
    existing.id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation]
    )
    session.scalars = AsyncMock(side_effect=[[], [revision_id], []])
    session.scalar = AsyncMock(return_value=existing)
    session.flush = AsyncMock()

    update_mock = AsyncMock()
    comment_update_mock = AsyncMock()
    create_check_mock = AsyncMock()
    with patch("app.services.github_publish.github_api.update_check_run", update_mock):
        with patch("app.services.github_publish.github_api.update_issue_comment", comment_update_mock):
            with patch("app.services.github_publish.github_api.create_check_run", create_check_mock):
                result = await github_publish.run_publish_job(session, publish_job_id=publish_job_id)

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_check_run_id == 50
    update_mock.assert_awaited_once()
    create_check_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_publish_job_for_review_run_skips_when_pending_exists():
    review_run_id = uuid.uuid4()
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[run, uuid.uuid4()])

    result = await github_publish.create_publish_job_for_review_run(
        session,
        review_run_id=review_run_id,
    )

    assert result is None
    session.add.assert_not_called()
