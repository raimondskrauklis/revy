# backend/tests/unit/test_github_review.py
"""GitHub review service — R4."""
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubIndexJobStatus,
    GitHubPullRequestState,
    GitHubReviewRunStatus,
    ReviewProfile,
)
from app.core.exceptions import ConflictError, ServiceUnavailableError
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services import github_review


@pytest.mark.asyncio
async def test_create_review_run_disabled_llm_raises():
    session = AsyncMock()
    with patch("app.services.github_review.settings") as mock_settings:
        mock_settings.llm_enabled = False
        with pytest.raises(ServiceUnavailableError) as exc:
            await github_review.create_review_run(
                session,
                workspace_id=uuid.uuid4(),
                repository_id=uuid.uuid4(),
                pull_request_id=uuid.uuid4(),
                revision_id=uuid.uuid4(),
            )
    assert exc.value.error_code == "llm_disabled"


@pytest.mark.asyncio
async def test_create_review_run_index_required_raises():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    with patch("app.services.github_review.settings") as mock_settings:
        mock_settings.llm_enabled = True
        mock_settings.embeddings_enabled = True
        mock_settings.github_api_enabled = True
        mock_settings.revy_llm_provider = "moonshot"
        with patch(
            "app.services.github_review.ensure_revision_access",
            AsyncMock(),
        ):
            with patch(
                "app.services.github_review.get_latest_index_job",
                AsyncMock(return_value=None),
            ):
                with pytest.raises(ConflictError) as exc:
                    await github_review.create_review_run(
                        session,
                        workspace_id=workspace_id,
                        repository_id=uuid.uuid4(),
                        pull_request_id=uuid.uuid4(),
                        revision_id=revision_id,
                    )
    assert exc.value.error_code == "index_required"


@pytest.mark.asyncio
async def test_create_review_run_review_in_progress_raises():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    index_job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.completed,
    )
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=uuid.uuid4())

    with patch("app.services.github_review.settings") as mock_settings:
        mock_settings.llm_enabled = True
        mock_settings.embeddings_enabled = True
        mock_settings.github_api_enabled = True
        mock_settings.revy_llm_provider = "moonshot"
        with patch("app.services.github_review.ensure_revision_access", AsyncMock()):
            with patch(
                "app.services.github_review.get_latest_index_job",
                AsyncMock(return_value=index_job),
            ):
                with pytest.raises(ConflictError) as exc:
                    await github_review.create_review_run(
                        session,
                        workspace_id=workspace_id,
                        repository_id=uuid.uuid4(),
                        pull_request_id=uuid.uuid4(),
                        revision_id=revision_id,
                    )
    assert exc.value.error_code == "review_in_progress"


def test_parse_finding_row_drops_style():
    assert github_review._parse_finding_row(
        {
            "severity": "info",
            "category": "style",
            "title": "Lint",
            "message": "Format",
        }
    ) is None


def test_parse_finding_row_accepts_valid():
    parsed = github_review._parse_finding_row(
        {
            "severity": "error",
            "category": "security",
            "title": "SQL injection",
            "message": "Unsanitized input",
            "file_path": "app/db.py",
            "start_line": 10,
        }
    )
    assert parsed is not None
    assert parsed["severity"] == FindingSeverity.error
    assert parsed["category"] == FindingCategory.security


@pytest.mark.asyncio
async def test_run_review_run_invalid_json_marks_failed():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.pending,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="Fix bug",
        state=GitHubPullRequestState.open,
        head_sha="abc",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    pull_request.id = pull_request_id

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision, pull_request])
    session.flush = AsyncMock()
    session.execute = AsyncMock()

    with patch(
        "app.services.github_review._collect_context_chunks",
        AsyncMock(return_value=[]),
    ):
        with patch(
            "app.services.github_review._call_llm",
            AsyncMock(return_value="not-json"),
        ):
            result = await github_review.run_review_run(session, review_run_id=review_run_id)

    assert result.status == GitHubReviewRunStatus.failed
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_run_review_run_happy_path_persists_findings():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.pending,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="Fix bug",
        state=GitHubPullRequestState.open,
        head_sha="abc",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    pull_request.id = pull_request_id

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision, pull_request])
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()

    llm_payload = json.dumps(
        {
            "findings": [
                {
                    "severity": "warning",
                    "category": "bug",
                    "title": "Edge case",
                    "message": "Handle empty list",
                },
                {
                    "severity": "info",
                    "category": "style",
                    "title": "Format",
                    "message": "Ignored",
                },
            ]
        }
    )

    with patch(
        "app.services.github_review._collect_context_chunks",
        AsyncMock(return_value=[]),
    ):
        with patch(
            "app.services.github_review._call_llm",
            AsyncMock(return_value=llm_payload),
        ):
            result = await github_review.run_review_run(session, review_run_id=review_run_id)

    assert result.status == GitHubReviewRunStatus.completed
    assert session.add.call_count == 1
