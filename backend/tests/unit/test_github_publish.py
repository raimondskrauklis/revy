# backend/tests/unit/test_github_publish.py
"""GitHub publish service — R6."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
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
from app.services.github_publish_formatter import PublishFormatResult


@pytest.fixture(autouse=True)
def _publish_formatter_defaults():
    with patch(
        "app.services.github_publish.get_latest_completed_index_job",
        AsyncMock(return_value=None),
    ):
        with patch(
            "app.services.github_publish._load_prior_inline_thread_map",
            AsyncMock(return_value={}),
        ):
            with patch(
                "app.services.github_publish._resolve_superseded_inline_threads",
                AsyncMock(),
            ):
                with patch(
                    "app.services.github_publish.build_publish_format_result_async",
                    AsyncMock(
                        return_value=PublishFormatResult(
                            check_summary="## Revy review\n\n**Confidence:** 5/5",
                            issue_comment="## Revy code review\n\nfull narrative",
                            confidence=5,
                            summary_json={"confidence": 5, "active_count": 0, "resolution": {}},
                        )
                    ),
                ):
                    yield


def test_compute_check_conclusion_neutral_on_critical():
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
    assert github_publish.compute_check_conclusion([group]) == "neutral"


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


def test_inline_publish_findings_statement_includes_warning():
    review_run_id = uuid.uuid4()
    stmt = github_publish.inline_publish_findings_statement(review_run_id=review_run_id)
    sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert FindingSeverity.warning.value in sql
    assert FindingSeverity.info.value in sql


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


def test_load_inline_thread_map_keeps_latest_comment_id():
    older = MagicMock()
    older.summary_json = {"github_inline_threads": {"fp": 100}}
    newer = MagicMock()
    newer.summary_json = {"github_inline_threads": {"fp": 999}}
    assert github_publish._load_inline_thread_map([older, newer]) == {"fp": 999}


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

    with patch(
        "app.services.github_publish.github_api.installation_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with patch("app.services.github_publish.github_api.create_check_run", AsyncMock(return_value=100)):
            with patch("app.services.github_publish.github_api.create_issue_comment", AsyncMock(return_value=200)):
                result = await github_publish.run_publish_job(session, publish_job_id=publish_job_id)

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_check_run_id == 100
    assert result.github_comment_id == 200


@pytest.mark.asyncio
async def test_run_publish_job_posts_formatted_issue_comment():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"
    formatted_comment = "## Revy code review\n\nfull narrative markdown"

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

    format_result = PublishFormatResult(
        check_summary="## Revy review\n\n**Confidence:** 5/5",
        issue_comment=formatted_comment,
        confidence=5,
        summary_json={"confidence": 5, "active_count": 0, "resolution": {}},
    )

    comment_mock = AsyncMock(return_value=200)
    with patch(
        "app.services.github_publish.build_publish_format_result_async",
        AsyncMock(return_value=format_result),
    ):
        with patch(
            "app.services.github_publish.github_api.installation_auth_headers",
            AsyncMock(return_value={"Authorization": "Bearer t"}),
        ):
            with patch("app.services.github_publish.github_api.create_check_run", AsyncMock(return_value=100)):
                with patch(
                    "app.services.github_publish.github_api.create_issue_comment",
                    comment_mock,
                ):
                    await github_publish.run_publish_job(session, publish_job_id=publish_job_id)

    comment_mock.assert_awaited_once()
    assert comment_mock.await_args.kwargs["body"] == formatted_comment
    assert not comment_mock.await_args.kwargs["body"].startswith("{")


@pytest.mark.asyncio
async def test_run_publish_job_updates_linked_pipeline_check_run():
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
        github_check_run_id=100,
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

    update_mock = AsyncMock()
    create_check_mock = AsyncMock()
    with patch(
        "app.services.github_publish.github_api.installation_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with patch("app.services.github_publish.github_api.update_check_run", update_mock):
            with patch("app.services.github_publish.github_api.create_issue_comment", AsyncMock(return_value=200)):
                with patch("app.services.github_publish.github_api.create_check_run", create_check_mock):
                    result = await github_publish.run_publish_job(session, publish_job_id=publish_job_id)

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_check_run_id == 100
    update_mock.assert_awaited_once()
    assert update_mock.await_args.kwargs["check_run_id"] == 100
    create_check_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_publish_job_posts_inline_for_warning_finding():
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
        github_check_run_id=100,
        github_comment_id=200,
        inline_comments_posted=False,
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

    finding = MagicMock()
    finding.file_path = "app/main.py"
    finding.start_line = 10
    finding.end_line = None
    finding.title = "Style"
    finding.message = "Prefer explicit return"
    finding.severity = FindingSeverity.warning
    finding.suggestion = "return True"
    finding.group_id = uuid.uuid4()

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp-warning",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Style",
        message="Prefer explicit return",
        file_path="app/main.py",
        last_seen_revision_id=revision_id,
    )
    group.id = finding.group_id

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation, group]
    )
    session.scalars = AsyncMock(side_effect=[[], [], [finding]])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    inline_mock = AsyncMock(return_value=9001)
    with patch(
        "app.services.github_publish._load_prior_inline_thread_map",
        AsyncMock(return_value={}),
    ):
        with patch(
            "app.services.github_publish._resolve_superseded_inline_threads",
            AsyncMock(),
        ):
            with patch(
                "app.services.github_publish.get_pipeline_run_for_review_run",
                AsyncMock(return_value=None),
            ):
                with patch(
                    "app.services.github_publish.github_api.installation_auth_headers",
                    AsyncMock(return_value={"Authorization": "Bearer t"}),
                ):
                    with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                        with patch("app.services.github_publish.github_api.update_issue_comment", AsyncMock()):
                            with patch(
                                "app.services.github_publish.github_api.create_pull_request_review_comment",
                                inline_mock,
                            ):
                                result = await github_publish.run_publish_job(
                                    session,
                                    publish_job_id=publish_job_id,
                                    persist_github_surface=True,
                                )

    assert result.status == GitHubPublishJobStatus.completed
    assert result.inline_comments_posted is True
    inline_mock.assert_awaited_once()
    body = inline_mock.await_args.kwargs["body"]
    assert "WARNING" in body
    assert "```suggestion" in body
    assert "return True" in body


@pytest.mark.asyncio
async def test_create_publish_job_for_review_run_reuses_pipeline_check_id():
    review_run_id = uuid.uuid4()
    pipeline_run_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=uuid.uuid4(),
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id

    pipeline_run = AsyncMock()
    pipeline_run.id = pipeline_run_id
    publish_job_id = uuid.uuid4()

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[run, None])
    session.get = AsyncMock(return_value=revision)
    session.add = MagicMock(side_effect=lambda job: setattr(job, "id", publish_job_id))
    session.flush = AsyncMock()

    with patch(
        "app.services.github_publish.get_pipeline_run_for_review_run",
        AsyncMock(return_value=pipeline_run),
    ):
        with patch(
            "app.services.github_publish.link_publish_job_to_pipeline",
            AsyncMock(),
        ):
            with patch(
                "app.services.github_publish.resolve_pipeline_github_check_run_id",
                AsyncMock(return_value=42),
            ):
                job_id = await github_publish.create_publish_job_for_review_run(
                    session,
                    review_run_id=review_run_id,
                )

    assert job_id == publish_job_id
    added_job = session.add.call_args[0][0]
    assert added_job.github_check_run_id == 42


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
        inline_comments_posted=True,
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
    with patch(
        "app.services.github_publish.github_api.installation_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with patch("app.services.github_publish.github_api.update_check_run", update_mock):
            with patch("app.services.github_publish.github_api.update_issue_comment", comment_update_mock):
                with patch("app.services.github_publish.github_api.create_check_run", create_check_mock):
                    result = await github_publish.run_publish_job(session, publish_job_id=publish_job_id)

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_check_run_id == 50
    update_mock.assert_awaited_once()
    create_check_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_publish_job_updates_prior_issue_comment_on_new_push():
    """R6-Q1: new head_sha reuses PR issue comment id from prior completed publish."""
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "def456"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
        github_check_run_id=100,
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
        revision_number=2,
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
        revision_count=2,
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

    comment_update_mock = AsyncMock()
    comment_create_mock = AsyncMock()
    with patch(
        "app.services.github_publish.find_prior_issue_comment_id_for_pull_request",
        AsyncMock(return_value=777),
    ):
        with patch(
            "app.services.github_publish.github_api.installation_auth_headers",
            AsyncMock(return_value={"Authorization": "Bearer t"}),
        ):
            with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                with patch(
                    "app.services.github_publish.github_api.update_issue_comment",
                    comment_update_mock,
                ):
                    with patch(
                        "app.services.github_publish.github_api.create_issue_comment",
                        comment_create_mock,
                    ):
                        result = await github_publish.run_publish_job(
                            session,
                            publish_job_id=publish_job_id,
                        )

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_comment_id == 777
    comment_update_mock.assert_awaited_once()
    assert comment_update_mock.await_args.kwargs["comment_id"] == 777
    comment_create_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_publish_job_posts_inline_when_prior_job_failed_before_inline():
    """R6-DEFER-01: Job B reuses Job A check run but posts inline when A never did."""
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
        status=GitHubPublishJobStatus.failed,
        github_check_run_id=50,
        github_comment_id=60,
        inline_comments_posted=False,
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

    finding = MagicMock()
    finding.file_path = "app/main.py"
    finding.start_line = 10
    finding.title = "Bug"
    finding.message = "Fix me"
    finding.severity = FindingSeverity.error
    finding.group_id = uuid.uuid4()

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp-error",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="Fix me",
        file_path="app/main.py",
        last_seen_revision_id=revision_id,
    )
    group.id = finding.group_id

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation, group]
    )
    session.scalars = AsyncMock(side_effect=[[], [finding]])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    inline_mock = AsyncMock(return_value=9002)
    create_check_mock = AsyncMock()
    with patch(
        "app.services.github_publish.find_prior_issue_comment_id_for_pull_request",
        AsyncMock(return_value=None),
    ):
        with patch(
            "app.services.github_publish.find_publish_job_for_head_sha",
            AsyncMock(return_value=existing),
        ):
            with patch(
                "app.services.github_publish.github_api.installation_auth_headers",
                AsyncMock(return_value={"Authorization": "Bearer t"}),
            ):
                with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                    with patch("app.services.github_publish.github_api.update_issue_comment", AsyncMock()):
                        with patch(
                            "app.services.github_publish.github_api.create_check_run",
                            create_check_mock,
                        ):
                            with patch(
                                "app.services.github_publish.github_api.create_pull_request_review_comment",
                                inline_mock,
                            ):
                                result = await github_publish.run_publish_job(
                                    session,
                                    publish_job_id=publish_job_id,
                                )

    create_check_mock.assert_not_awaited()

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_check_run_id == 50
    assert result.inline_comments_posted is True
    inline_mock.assert_awaited_once()


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


@pytest.mark.asyncio
async def test_resolve_publish_job_id_for_review_run_reuses_pending_job():
    review_run_id = uuid.uuid4()
    existing_job_id = uuid.uuid4()
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[run, uuid.uuid4(), existing_job_id])

    job_id, created = await github_publish.resolve_publish_job_id_for_review_run(
        session,
        review_run_id=review_run_id,
    )

    assert job_id == existing_job_id
    assert created is False
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_publish_job_returns_existing_pending_job():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    pending_job_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=uuid.uuid4(),
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id

    pending_job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha="abc",
        status=GitHubPublishJobStatus.pending,
    )
    pending_job.id = pending_job_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=pending_job_id)
    session.get = AsyncMock(side_effect=[run, revision, pending_job])

    with patch("app.services.github_publish.settings") as mock_settings:
        mock_settings.github_api_enabled = True
        with patch(
            "app.services.github_publish.ensure_revision_access",
            AsyncMock(),
        ):
            result = await github_publish.create_publish_job(
                session,
                workspace_id=workspace_id,
                repository_id=uuid.uuid4(),
                pull_request_id=uuid.uuid4(),
                revision_id=revision_id,
                review_run_id=review_run_id,
            )

    assert result.id == pending_job_id
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_run_publish_job_posts_inline_after_surface_checkpoint():
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
        github_check_run_id=100,
        github_comment_id=200,
        inline_comments_posted=False,
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

    finding = MagicMock()
    finding.file_path = "app/main.py"
    finding.start_line = 10
    finding.title = "Bug"
    finding.message = "Fix me"
    finding.severity = FindingSeverity.error
    finding.group_id = uuid.uuid4()

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp-error-2",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="Fix me",
        file_path="app/main.py",
        last_seen_revision_id=revision_id,
    )
    group.id = finding.group_id

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation, group]
    )
    session.scalars = AsyncMock(side_effect=[[], [revision_id], [finding]])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    inline_mock = AsyncMock(return_value=9003)
    with patch(
        "app.services.github_publish.get_pipeline_run_for_review_run",
        AsyncMock(return_value=None),
    ):
        with patch(
            "app.services.github_publish.github_api.installation_auth_headers",
            AsyncMock(return_value={"Authorization": "Bearer t"}),
        ):
            with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                with patch("app.services.github_publish.github_api.update_issue_comment", AsyncMock()):
                    with patch(
                        "app.services.github_publish.github_api.create_pull_request_review_comment",
                        inline_mock,
                    ):
                        result = await github_publish.run_publish_job(
                            session,
                            publish_job_id=publish_job_id,
                            persist_github_surface=True,
                        )

    assert result.status == GitHubPublishJobStatus.completed
    assert result.inline_comments_posted is True
    inline_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_publish_job_resolves_superseded_threads_when_inline_already_posted():
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
        github_check_run_id=100,
        github_comment_id=200,
        inline_comments_posted=True,
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

    resolve_mock = AsyncMock()
    inline_mock = AsyncMock()
    with patch(
        "app.services.github_publish._resolve_superseded_inline_threads",
        resolve_mock,
    ):
        with patch(
            "app.services.github_publish.get_pipeline_run_for_review_run",
            AsyncMock(return_value=None),
        ):
            with patch(
                "app.services.github_publish.github_api.installation_auth_headers",
                AsyncMock(return_value={"Authorization": "Bearer t"}),
            ):
                with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                    with patch("app.services.github_publish.github_api.update_issue_comment", AsyncMock()):
                        with patch(
                            "app.services.github_publish.github_api.create_pull_request_review_comment",
                            inline_mock,
                        ):
                            result = await github_publish.run_publish_job(
                                session,
                                publish_job_id=publish_job_id,
                            )

    assert result.status == GitHubPublishJobStatus.completed
    resolve_mock.assert_awaited_once()
    inline_mock.assert_not_awaited()


def _publish_job_context():
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

    return publish_job_id, session, job


@pytest.mark.asyncio
async def test_run_publish_job_marks_failed_on_permanent_error_when_persisting():
    publish_job_id, session, job = _publish_job_context()
    request = httpx.Request("POST", "https://api.github.com/check-runs")
    response = httpx.Response(400, request=request)
    error = httpx.HTTPStatusError("bad request", request=request, response=response)

    with patch(
        "app.services.github_publish.github_api.installation_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with patch(
            "app.services.github_publish.github_api.create_check_run",
            AsyncMock(side_effect=error),
        ):
            result = await github_publish.run_publish_job(
                session,
                publish_job_id=publish_job_id,
                persist_github_surface=True,
            )

    assert result is job
    assert result.status == GitHubPublishJobStatus.failed
    assert result.error_message == "bad request"


@pytest.mark.asyncio
async def test_run_publish_job_raises_retryable_error_when_persisting():
    publish_job_id, session, job = _publish_job_context()
    request = httpx.Request("POST", "https://api.github.com/check-runs")
    response = httpx.Response(503, request=request)
    error = httpx.HTTPStatusError("unavailable", request=request, response=response)

    with patch(
        "app.services.github_publish.github_api.installation_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with patch(
            "app.services.github_publish.github_api.create_check_run",
            AsyncMock(side_effect=error),
        ):
            with pytest.raises(github_publish.PublishJobRetryableError):
                await github_publish.run_publish_job(
                    session,
                    publish_job_id=publish_job_id,
                    persist_github_surface=True,
                )

    assert job.status == GitHubPublishJobStatus.processing
