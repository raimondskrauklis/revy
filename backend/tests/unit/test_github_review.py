# backend/tests/unit/test_github_review.py
"""GitHub review service — R4."""
import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubIndexJobStatus,
    GitHubIndexMode,
    GitHubPullRequestState,
    GitHubReviewJudgeStatus,
    GitHubReviewRunStatus,
    ReviewProfile,
)
from app.core.exceptions import ConflictError, ServiceUnavailableError, ValidationError
from app.core.worker_retries import WorkerRetryableError
from app.models.github_finding import GitHubFindingORM
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_review_run import GitHubReviewRunORM
from app.schemas.github_review import GitHubReviewRunResponse
from app.services import github_review
from app.services.model_policy import ModelRef


def _completed_index_job(*, revision_id: uuid.UUID, workspace_id: uuid.UUID) -> GitHubIndexJobORM:
    return GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.completed,
        index_mode=GitHubIndexMode.diff,
    )


def _review_context_pack() -> github_review.ReviewContextPack:
    return github_review.ReviewContextPack(
        prompt="review prompt",
        manifest={"index_mode": "diff", "changed_files": ["app/main.py"]},
    )


def _session_execute_mock() -> AsyncMock:
    result = MagicMock()
    result.rowcount = 1
    return AsyncMock(return_value=result)


@pytest.mark.asyncio
async def test_create_review_run_disabled_llm_raises():
    session = AsyncMock()
    with patch("app.services.github_review.settings") as mock_settings:
        mock_settings.reviewer_llm_enabled.return_value = False
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
        mock_settings.reviewer_llm_enabled.return_value = True
        mock_settings.embeddings_enabled = True
        mock_settings.github_api_enabled = True
        mock_settings.revy_llm_provider = "moonshot"
        with patch(
            "app.services.github_review.ensure_revision_access",
            AsyncMock(),
        ):
            with patch(
                "app.services.github_review.index_job_in_progress",
                AsyncMock(return_value=False),
            ):
                with patch(
                    "app.services.github_review.get_latest_completed_index_job",
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
async def test_create_review_run_deep_profile_requires_full_index():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    index_job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.completed,
        index_mode=GitHubIndexMode.diff,
    )
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    with patch("app.services.github_review.settings") as mock_settings:
        mock_settings.reviewer_llm_enabled.return_value = True
        mock_settings.embeddings_enabled = True
        mock_settings.github_api_enabled = True
        mock_settings.revy_llm_provider = "moonshot"
        with patch("app.services.github_review.ensure_revision_access", AsyncMock()):
            with patch(
                "app.services.github_review.index_job_in_progress",
                AsyncMock(return_value=False),
            ):
                with patch(
                    "app.services.github_review.get_latest_completed_index_job",
                    AsyncMock(return_value=index_job),
                ):
                    with pytest.raises(ConflictError) as exc:
                        await github_review.create_review_run(
                            session,
                            workspace_id=workspace_id,
                            repository_id=uuid.uuid4(),
                            pull_request_id=uuid.uuid4(),
                            revision_id=revision_id,
                            profile=ReviewProfile.deep,
                        )
    assert exc.value.error_code == "index_mode_mismatch"


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
        mock_settings.reviewer_llm_enabled.return_value = True
        mock_settings.embeddings_enabled = True
        mock_settings.github_api_enabled = True
        mock_settings.revy_llm_provider = "moonshot"
        with patch("app.services.github_review.ensure_revision_access", AsyncMock()):
            with patch(
                "app.services.github_review.index_job_in_progress",
                AsyncMock(return_value=False),
            ):
                with patch(
                    "app.services.github_review.get_latest_completed_index_job",
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
    row, reason = github_review._parse_finding_row(
        {
            "severity": "info",
            "category": "style",
            "title": "Lint",
            "message": "Format",
        }
    )
    assert row is None
    assert reason == "style_category"


def test_parse_finding_row_accepts_valid():
    parsed, reason = github_review._parse_finding_row(
        {
            "severity": "error",
            "category": "security",
            "title": "SQL injection",
            "message": "Unsanitized input",
            "file_path": "app/db.py",
            "start_line": 10,
        }
    )
    assert reason is None
    assert parsed is not None
    assert parsed["severity"] == FindingSeverity.error
    assert parsed["category"] == FindingCategory.security


def test_parse_finding_row_accepts_suggestion():
    parsed, reason = github_review._parse_finding_row(
        {
            "severity": "error",
            "category": "bug",
            "title": "Typo",
            "message": "Wrong variable",
            "file_path": "app/main.py",
            "start_line": 4,
            "suggestion": "return True",
        }
    )
    assert reason is None
    assert parsed is not None
    assert parsed["suggestion"] == "return True"


def test_parse_finding_row_drops_multiline_suggestion():
    parsed, reason = github_review._parse_finding_row(
        {
            "severity": "error",
            "category": "bug",
            "title": "Typo",
            "message": "Wrong variable",
            "file_path": "app/main.py",
            "start_line": 4,
            "suggestion": "line one\nline two",
        }
    )
    assert reason is None
    assert parsed is not None
    assert "suggestion" not in parsed


def test_parse_finding_row_normalizes_end_line_zero():
    parsed, reason = github_review._parse_finding_row(
        {
            "severity": "error",
            "category": "bug",
            "title": "Typo",
            "message": "Wrong variable",
            "file_path": "app/main.py",
            "start_line": 4,
            "end_line": 0,
            "suggestion": "return True",
        }
    )
    assert reason is None
    assert parsed is not None
    assert parsed["end_line"] is None
    assert parsed["suggestion"] == "return True"


@pytest.mark.asyncio
async def test_run_review_run_skips_non_pending_status():
    review_run_id = uuid.uuid4()
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.processing,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    session = AsyncMock()
    session.get = AsyncMock(return_value=run)
    failed_start = MagicMock()
    failed_start.rowcount = 0
    session.execute = AsyncMock(return_value=failed_start)
    session.refresh = AsyncMock()

    with patch("app.services.github_review.prepare_review_context", AsyncMock()) as context_mock:
        result = await github_review.run_review_run(session, review_run_id=review_run_id)

    assert result.run.status == GitHubReviewRunStatus.processing
    context_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_review_run_stale_model_policy_marks_failed():
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

    index_job = _completed_index_job(revision_id=revision_id, workspace_id=workspace_id)
    with patch(
        "app.services.github_review.get_latest_completed_index_job",
        AsyncMock(return_value=index_job),
    ):
        with patch(
            "app.services.github_review.prepare_review_context",
            AsyncMock(return_value=_review_context_pack()),
        ):
            with patch(
                "app.services.github_review.resolve_model",
                AsyncMock(
                    side_effect=ValidationError(
                        message="Workspace model override is no longer valid",
                        field="reviewer_standard",
                    )
                ),
            ):
                result = await github_review.run_review_run(session, review_run_id=review_run_id)

    assert result.run.status == GitHubReviewRunStatus.failed
    assert "no longer valid" in (result.run.error_message or "")


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
    session.execute = _session_execute_mock()

    index_job = _completed_index_job(revision_id=revision_id, workspace_id=workspace_id)
    with patch(
        "app.services.github_review.get_latest_completed_index_job",
        AsyncMock(return_value=index_job),
    ):
        with patch(
            "app.services.github_review.prepare_review_context",
            AsyncMock(return_value=_review_context_pack()),
        ):
            with patch(
                "app.services.github_review.resolve_model",
                AsyncMock(return_value=ModelRef(provider="moonshot", model_id="kimi-k2.7-code")),
            ):
                with patch(
                    "app.services.github_review._call_llm",
                    AsyncMock(return_value="not-json"),
                ):
                    result = await github_review.run_review_run(session, review_run_id=review_run_id)

    assert result.run.status == GitHubReviewRunStatus.failed
    assert result.run.error_message is not None


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
    session.execute = _session_execute_mock()
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

    index_job = _completed_index_job(revision_id=revision_id, workspace_id=workspace_id)
    with patch(
        "app.services.github_review.get_latest_completed_index_job",
        AsyncMock(return_value=index_job),
    ):
        with patch(
            "app.services.github_review.prepare_review_context",
            AsyncMock(return_value=_review_context_pack()),
        ):
            with patch(
                "app.services.github_review.resolve_model",
                AsyncMock(return_value=ModelRef(provider="moonshot", model_id="kimi-k2.7-code")),
            ):
                with patch(
                    "app.services.github_review._call_llm",
                    AsyncMock(return_value=llm_payload),
                ):
                    result = await github_review.run_review_run(session, review_run_id=review_run_id)

    assert result.run.status == GitHubReviewRunStatus.completed
    assert session.add.call_count == 1


@pytest.mark.asyncio
async def test_run_review_run_persists_evidence_snippet_from_diff():
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
    session.execute = _session_execute_mock()

    added: list = []
    session.add = MagicMock(side_effect=lambda obj: added.append(obj))

    patch_body = "@@ -1,1 +1,2 @@\n-old\n+new_line\n"
    context_pack = github_review.ReviewContextPack(
        prompt="review prompt",
        manifest={"index_mode": "diff"},
        patches_by_file={"app/main.py": patch_body},
    )
    llm_payload = json.dumps(
        {
            "findings": [
                {
                    "severity": "error",
                    "category": "bug",
                    "title": "Bug",
                    "message": "Bad change",
                    "file_path": "app/main.py",
                    "start_line": 1,
                },
            ]
        }
    )

    index_job = _completed_index_job(revision_id=revision_id, workspace_id=workspace_id)
    with patch(
        "app.services.github_review.get_latest_completed_index_job",
        AsyncMock(return_value=index_job),
    ):
        with patch(
            "app.services.github_review.prepare_review_context",
            AsyncMock(return_value=context_pack),
        ):
            with patch(
                "app.services.github_review.resolve_model",
                AsyncMock(return_value=ModelRef(provider="moonshot", model_id="kimi-k2.7-code")),
            ):
                with patch(
                    "app.services.github_review._call_llm",
                    AsyncMock(return_value=llm_payload),
                ):
                    result = await github_review.run_review_run(session, review_run_id=review_run_id)

    assert result.run.status == GitHubReviewRunStatus.completed
    assert len(added) == 1
    assert added[0].evidence_snippet is not None
    assert "new_line" in added[0].evidence_snippet


@pytest.mark.asyncio
async def test_run_review_run_accepts_profile_string_from_db():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.pending,
        profile="standard",
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
    session.execute = _session_execute_mock()
    session.add = MagicMock()

    index_job = _completed_index_job(revision_id=revision_id, workspace_id=workspace_id)
    with patch(
        "app.services.github_review.get_latest_completed_index_job",
        AsyncMock(return_value=index_job),
    ):
        with patch(
            "app.services.github_review.prepare_review_context",
            AsyncMock(return_value=_review_context_pack()),
        ):
            with patch(
                "app.services.github_review.resolve_model",
                AsyncMock(return_value=ModelRef(provider="moonshot", model_id="kimi-k2.7-code")),
            ):
                with patch(
                    "app.services.github_review._call_llm",
                    AsyncMock(return_value='{"findings": []}'),
                ) as llm_mock:
                    result = await github_review.run_review_run(session, review_run_id=review_run_id)

    assert result.run.status == GitHubReviewRunStatus.completed
    assert llm_mock.await_args.kwargs["profile"] == "standard"


@pytest.mark.asyncio
async def test_run_review_run_raises_retryable_on_transient_llm_failure():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.pending,
        profile="standard",
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

    response = httpx.Response(503, request=httpx.Request("POST", "https://api.moonshot.ai"))
    transient_error = httpx.HTTPStatusError("unavailable", request=response.request, response=response)

    index_job = _completed_index_job(revision_id=revision_id, workspace_id=workspace_id)
    with patch(
        "app.services.github_review.get_latest_completed_index_job",
        AsyncMock(return_value=index_job),
    ):
        with patch(
            "app.services.github_review.prepare_review_context",
            AsyncMock(return_value=_review_context_pack()),
        ):
            with patch(
                "app.services.github_review.resolve_model",
                AsyncMock(return_value=ModelRef(provider="moonshot", model_id="kimi-k2.7-code")),
            ):
                with patch(
                    "app.services.github_review._call_llm",
                    AsyncMock(side_effect=transient_error),
                ):
                    with pytest.raises(WorkerRetryableError):
                        await github_review.run_review_run(session, review_run_id=review_run_id)


def test_build_unified_diff_truncates_largest_files_first():
    from app.integrations.github_api import CompareFileChange

    small_patch = "+" + ("a" * 100)
    large_patch = "+" + ("b" * 200_000)
    files = (
        CompareFileChange(filename="small.py", status="modified", patch=small_patch),
        CompareFileChange(filename="large.py", status="modified", patch=large_patch),
    )

    diff, truncated, omitted = github_review.build_unified_diff(files, max_bytes=8_000)

    assert truncated is True
    assert omitted == ["large.py"]
    assert "small.py" in diff
    assert "large.py" not in diff


def test_build_unified_diff_default_cap_allows_large_patch():
    from app.integrations.github_api import CompareFileChange

    patch_body = "+" + ("x" * 200_000)
    files = (CompareFileChange(filename="big.py", status="modified", patch=patch_body),)

    diff, truncated, omitted = github_review.build_unified_diff(files)

    assert truncated is False
    assert omitted == []
    assert "big.py" in diff


def test_build_review_prompt_engineering_context_before_diff():
    prompt = github_review._build_review_prompt(
        pr_title="Title",
        pr_body=None,
        head_sha="abc",
        base_ref="main",
        head_ref="feat",
        index_mode=GitHubIndexMode.diff,
        changed_files=["backend/main.py"],
        unified_diff="@@ patch",
        supplemental=[],
        engineering_block="## Locked decisions\n\n**RCX-D8**",
    )
    eng_pos = prompt.index("Engineering context (authoritative)")
    diff_pos = prompt.index("Unified diff (primary)")
    assert eng_pos < diff_pos
    assert "RCX-D8" in prompt
    assert "override generic API advice" in prompt


@pytest.mark.asyncio
async def test_prepare_review_context_populates_engineering_manifest():
    from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
    from app.services.engineering_context.pack import EngineeringContextPack

    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="headsha",
        base_sha="basesha",
    )
    revision.id = revision_id

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="RCX",
        state=GitHubPullRequestState.open,
        head_sha="headsha",
        head_ref="feat",
        base_ref="main",
        revision_count=1,
    )

    index_job = _completed_index_job(revision_id=revision_id, workspace_id=workspace_id)
    engineering_pack = EngineeringContextPack(
        active_program="review-engineering-context",
        lock_ids=["RCX-D8"],
        inject_text="## Locked decisions\n",
        deduped_paths=["docs/a.md"],
    )
    session = AsyncMock()

    with patch(
        "app.services.github_review._fetch_compare_for_review",
        AsyncMock(return_value=(None, "compare_skipped")),
    ):
        with patch(
            "app.services.github_review._resolve_github_repo_for_revision",
            AsyncMock(return_value=(MagicMock(github_installation_id=99), "org", "repo")),
        ):
            with patch(
                "app.services.github_review.build_engineering_context_pack",
                AsyncMock(return_value=engineering_pack),
            ):
                with patch(
                    "app.services.github_review._collect_supplemental_chunks",
                    AsyncMock(return_value=[]),
                ):
                    pack = await github_review.prepare_review_context(
                        session,
                        workspace_id=workspace_id,
                        repository_id=repository_id,
                        pull_request_id=pull_request_id,
                        revision=revision,
                        pull_request=pull_request,
                        index_job=index_job,
                    )

    assert pack.manifest["engineering_context_injected"] is True
    assert pack.manifest["lock_ids_extracted"] == ["RCX-D8"]
    assert pack.manifest["engineering_context_deduped_paths"] == ["docs/a.md"]
    assert "Engineering context (authoritative)" in pack.prompt


def test_normalize_finding_start_line():
    assert github_review.normalize_finding_start_line(12) == 12
    assert github_review.normalize_finding_start_line("15") == 15
    assert github_review.normalize_finding_start_line(0) is None
    assert github_review.normalize_finding_start_line("abc") is None


def test_normalize_finding_end_line():
    assert github_review.normalize_finding_end_line(12) == 12
    assert github_review.normalize_finding_end_line("15") == 15
    assert github_review.normalize_finding_end_line(0) is None
    assert github_review.normalize_finding_end_line("abc") is None


def test_parse_finding_row_accepts_string_end_line():
    parsed, reason = github_review._parse_finding_row(
        {
            "severity": "warning",
            "category": "bug",
            "title": "t",
            "message": "m",
            "start_line": "10",
            "end_line": "12",
        }
    )
    assert reason is None
    assert parsed is not None
    assert parsed["start_line"] == 10
    assert parsed["end_line"] == 12


def test_normalize_patch_file_key():
    assert github_review.normalize_patch_file_key("./app/main.py") == "app/main.py"
    assert github_review.normalize_patch_file_key("app\\main.py") == "app/main.py"


def test_lookup_patch_for_file_normalized_key():
    patches = {"app/main.py": "@@ patch\n+line\n"}
    assert github_review.lookup_patch_for_file(patches, "./app/main.py") == patches["app/main.py"]
    assert github_review.lookup_patch_for_file(patches, "app\\main.py") == patches["app/main.py"]


def test_extract_evidence_from_patch_around_line():
    patch = """@@ -10,3 +10,4 @@
 def foo():
-    old()
+    new_call()
     return x
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=12)
    assert snippet is not None
    assert "new_call" in snippet


def test_extract_evidence_from_patch_includes_removed_line():
    patch = """@@ -10,3 +10,4 @@
 def foo():
-    old()
+    new_call()
     return x
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=11)
    assert snippet is not None
    assert "-    old()" in snippet


def test_extract_evidence_from_patch_multiple_consecutive_removed_lines():
    patch = """@@ -10,4 +10,2 @@
 def foo():
-    first_removed()
-    second_removed()
+    new_call()
     return x
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=12)
    assert snippet is not None
    assert "-    first_removed()" in snippet
    assert "-    second_removed()" in snippet
    assert "new_call" in snippet


def test_extract_evidence_from_patch_removal_only_hunk():
    patch = """@@ -8,3 +8,0 @@
-    only_removed()
-    also_removed()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=9)
    assert snippet is not None
    assert "-    only_removed()" in snippet
    assert "-    also_removed()" in snippet


def test_extract_evidence_from_patch_context_in_window_still_includes_removed():
    """Context lines in the window must not hide removed-line evidence (revybot #56)."""
    patch = """@@ -10,4 +10,4 @@
 def foo():
     unchanged_context()
-    first_removed()
-    second_removed()
+    new_call()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=12)
    assert snippet is not None
    assert "unchanged_context()" in snippet
    assert "-    first_removed()" in snippet
    assert "-    second_removed()" in snippet
    assert "new_call" in snippet


def test_extract_evidence_from_patch_spacer_in_window_does_not_drop_pending_minus():
    """Context between - and + in the window must not clear pending removed lines."""
    spacer_lines = "\n".join(f" spacer{i}" for i in range(76))
    patch = f"""@@ -1,100 +1,100 @@
-removed_at_old_2()
{spacer_lines}
+added_at_new_79()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=79)
    assert snippet is not None
    assert "-removed_at_old_2()" in snippet
    assert "added_at_new_79" in snippet


def test_extract_evidence_from_patch_duplicate_removed_lines_preserved():
    patch = """@@ -1,3 +1,1 @@
-    dup()
-    dup()
+    one()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=1)
    assert snippet is not None
    assert snippet.count("dup()") == 2


def test_extract_evidence_from_patch_minus_in_old_window_when_plus_outside_new_window():
    patch = """@@ -94,1 +54,1 @@
-removed_at_old_95()
+added_at_new_55()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=95)
    assert snippet is not None
    assert "-removed_at_old_95()" in snippet
    assert "added_at_new_55" not in snippet


def test_extract_evidence_from_patch_unrelated_minus_not_paired_with_later_plus():
    patch = """@@ -1,4 +1,4 @@
- unrelated_old()
 context()
- target_old()
+ target_new()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=3)
    assert snippet is not None
    assert "- unrelated_old()" not in snippet
    assert "- target_old()" in snippet
    assert "target_new" in snippet


def test_extract_evidence_from_patch_hunk_boundary_flushes_orphan_minus():
    patch = """@@ -1,1 +1,1 @@
- orphan_in_hunk1()
@@ -94,1 +55,1 @@
- removed_at_old_95()
+ added_at_new_55()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=55)
    assert snippet is not None
    assert "orphan_in_hunk1" not in snippet
    assert "- removed_at_old_95()" in snippet
    assert "added_at_new_55" in snippet


def test_extract_evidence_from_patch_empty_line_in_hunk():
    patch = """@@ -1,3 +1,3 @@
-removed()
 
+added()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=2)
    assert snippet is not None
    assert "-removed()" in snippet
    assert "added" in snippet


def test_extract_evidence_from_patch_old_new_line_drift_in_hunk():
    patch = """@@ -95,1 +55,1 @@
-removed_at_old_95()
+added_at_new_55()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=55)
    assert snippet is not None
    assert "-removed_at_old_95()" in snippet
    assert "added_at_new_55" in snippet


def test_extract_evidence_from_patch_orphan_deletion_before_separate_change():
    patch = """@@ -5,1 +5,1 @@
- orphan_delete_old_5()
 context()
- target_old()
+ target_new()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=5)
    assert snippet is not None
    assert "- orphan_delete_old_5()" in snippet


def test_extract_evidence_from_patch_cross_hunk_orphan_does_not_leak():
    patch = """@@ -4,2 +4,1 @@
- unrelated_hunk1_old_5()
 context()
@@ -50,2 +10,2 @@
- target_old()
+ target_new()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=11)
    assert snippet is not None
    assert "unrelated_hunk1" not in snippet
    assert "- target_old()" in snippet
    assert "target_new" in snippet


def test_extract_evidence_from_patch_removal_only_hunk_with_separate_minus_groups():
    patch = """@@ -5,3 +5,1 @@
- first_orphan()
 context()
- second_orphan()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=5)
    assert snippet is not None
    assert "- first_orphan()" in snippet
    assert "- second_orphan()" in snippet


def test_extract_evidence_from_patch_multi_hunk_minus_in_old_window_plus_outside_window():
    patch = """@@ -1,1 +1,1 @@
- stray_in_hunk1()
@@ -94,1 +54,1 @@
- removed_at_old_95()
+ added_at_new_55()
"""
    snippet = github_review.extract_evidence_from_patch(patch, start_line=95)
    assert snippet is not None
    assert "stray_in_hunk1" not in snippet
    assert "- removed_at_old_95()" in snippet
    assert "added_at_new_55" not in snippet


def test_resolve_judge_code_context_returns_snippet_and_patch():
    patches = {
        "app/main.py": "@@ -1,1 +1,2 @@\n-old\n+new_line\n",
    }
    ctx = github_review.resolve_judge_code_context(
        file_path="app/main.py",
        start_line=1,
        patches_by_file=patches,
        supplemental_top_by_file={},
        patch_max_chars=100,
    )
    assert ctx.evidence_snippet is not None
    assert "new_line" in ctx.evidence_snippet
    assert ctx.file_patch is not None
    assert "new_line" in ctx.file_patch


def test_resolve_judge_code_context_lineless_still_has_patch():
    patches = {"src/handler.py": "@@ -0,0 +1,3 @@\n+line1\n+line2\n"}
    ctx = github_review.resolve_judge_code_context(
        file_path="src/handler.py",
        start_line=None,
        patches_by_file=patches,
        supplemental_top_by_file={},
    )
    assert ctx.file_patch is not None
    assert "line1" in ctx.file_patch


def test_resolve_judge_code_context_missing_patch():
    ctx = github_review.resolve_judge_code_context(
        file_path="missing.py",
        start_line=1,
        patches_by_file={},
        supplemental_top_by_file={},
    )
    assert ctx.evidence_snippet is None
    assert ctx.file_patch is None


def test_resolve_evidence_snippet_prefers_diff_over_supplemental():
    from app.schemas.github_indexing import GitHubChunkSearchResult

    chunk = GitHubChunkSearchResult(
        id=uuid.uuid4(),
        file_path="app/main.py",
        chunk_index=0,
        content="retrieval fallback",
        score=0.5,
    )
    supplemental = {
        "app/main.py": github_review.ScopedChunkHit(
            hit=chunk,
            lens="logic bugs",
            in_diff=True,
            rank=1,
        )
    }
    snippet = github_review.resolve_evidence_snippet(
        file_path="app/main.py",
        start_line=2,
        patches_by_file={"app/main.py": "@@ -1,1 +1,2 @@\n-old\n+new_line\n"},
        supplemental_top_by_file=supplemental,
    )
    assert snippet is not None
    assert "new_line" in snippet
    assert "retrieval fallback" not in snippet


def test_resolve_evidence_snippet_uses_supplemental_when_hunk_misses():
    from app.schemas.github_indexing import GitHubChunkSearchResult

    chunk = GitHubChunkSearchResult(
        id=uuid.uuid4(),
        file_path="app/main.py",
        chunk_index=0,
        content="retrieval fallback",
        score=0.5,
    )
    supplemental = {
        "app/main.py": github_review.ScopedChunkHit(
            hit=chunk,
            lens="logic bugs",
            in_diff=True,
            rank=1,
        )
    }
    snippet = github_review.resolve_evidence_snippet(
        file_path="app/main.py",
        start_line=99,
        patches_by_file={"app/main.py": "@@ -1,1 +1,2 @@\n-old\n+new_line\n"},
        supplemental_top_by_file=supplemental,
    )
    assert snippet == "retrieval fallback"


def test_resolve_evidence_snippet_uses_supplemental_without_patch():
    from app.schemas.github_indexing import GitHubChunkSearchResult

    chunk = GitHubChunkSearchResult(
        id=uuid.uuid4(),
        file_path="app/other.py",
        chunk_index=0,
        content="chunk body",
        score=0.5,
    )
    supplemental = {
        "app/other.py": github_review.ScopedChunkHit(
            hit=chunk,
            lens="logic bugs",
            in_diff=False,
            rank=1,
        )
    }
    snippet = github_review.resolve_evidence_snippet(
        file_path="app/other.py",
        start_line=10,
        patches_by_file={},
        supplemental_top_by_file=supplemental,
    )
    assert snippet == "chunk body"


def test_build_review_prompt_orders_diff_before_supplemental():
    from app.schemas.github_indexing import GitHubChunkSearchResult

    chunk = GitHubChunkSearchResult(
        id=uuid.uuid4(),
        file_path="app/main.py",
        chunk_index=0,
        content="helper context",
        score=0.9,
    )
    supplemental = [
        github_review.ScopedChunkHit(hit=chunk, lens="logic bugs", in_diff=True, rank=1),
    ]
    prompt = github_review._build_review_prompt(
        pr_title="Fix handler",
        pr_body=None,
        head_sha="head123",
        base_ref="main",
        head_ref="feature",
        index_mode=GitHubIndexMode.diff,
        changed_files=["app/main.py"],
        unified_diff="@@ patch @@",
        supplemental=supplemental,
    )

    diff_pos = prompt.index("Unified diff (primary):")
    supplemental_pos = prompt.index("Supplemental context (bounded):")
    assert diff_pos < supplemental_pos
    assert "@@ patch @@" in prompt
    assert "helper context" in prompt


def test_build_review_prompt_includes_pr_body_when_set():
    prompt = github_review._build_review_prompt(
        pr_title="Fix handler",
        pr_body="Fixes #42",
        head_sha="head123",
        base_ref="main",
        head_ref="feature",
        index_mode=GitHubIndexMode.diff,
        changed_files=["app/main.py"],
        unified_diff="+change",
        supplemental=[],
    )
    assert "PR body:" in prompt
    assert "Fixes #42" in prompt


def test_build_review_prompt_omits_pr_body_when_none():
    prompt = github_review._build_review_prompt(
        pr_title="Fix handler",
        pr_body=None,
        head_sha="head123",
        base_ref="main",
        head_ref="feature",
        index_mode=GitHubIndexMode.diff,
        changed_files=["app/main.py"],
        unified_diff="+change",
        supplemental=[],
    )
    assert "PR body:" not in prompt


def test_retrieval_file_paths_excludes_tests_unless_pr_touches_tests():
    changed = frozenset({"app/main.py", "tests/unit/test_main.py"})
    assert "tests/unit/test_main.py" in github_review._retrieval_file_paths(changed)

    only_app = frozenset({"app/main.py"})
    assert github_review._retrieval_file_paths(only_app) == frozenset({"app/main.py"})


def test_parse_finding_rows_returns_parse_report():
    rows, report = github_review.parse_finding_rows(
        [
            {
                "severity": "error",
                "category": "bug",
                "title": "Bug",
                "message": "Details",
            },
            {
                "severity": "info",
                "category": "style",
                "title": "Format",
                "message": "Ignored",
            },
            "not-a-dict",
        ]
    )

    assert len(rows) == 1
    assert report["parsed_count"] == 1
    assert report["dropped_count"] == 2
    assert report["drop_reasons"]["style_category"] == 1
    assert report["drop_reasons"]["invalid_row"] == 1


def test_build_retrieval_manifest_includes_sc3_defaults():
    manifest = github_review.build_retrieval_manifest(
        index_mode=GitHubIndexMode.diff,
        changed_files=["app/main.py"],
        diff_truncated=False,
        omitted_files=[],
        fallback_reason=None,
        supplemental=[],
    )

    assert manifest["structural_context_mode"] == "none"
    assert manifest["structural_context_attempted"] is False
    assert manifest["changed_symbols"] == []


def test_build_retrieval_manifest_includes_engineering_context_defaults():
    manifest = github_review.build_retrieval_manifest(
        index_mode=GitHubIndexMode.diff,
        changed_files=["app/main.py"],
        diff_truncated=False,
        omitted_files=[],
        fallback_reason=None,
        supplemental=[],
    )

    assert manifest["engineering_context_injected"] is False
    assert manifest["engineering_context_bytes"] == 0
    assert manifest["diff_max_bytes"] == 524288
    assert manifest["unified_diff_bytes"] == 0
    assert manifest["active_program"] is None
    assert manifest["lock_ids_extracted"] == []
    assert manifest["engineering_context_deduped_paths"] == []
    assert manifest["engineering_context_errors"] == []


def test_review_run_polish_defaults():
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.pending,
        profile=ReviewProfile.standard,
    )
    run.id = uuid.uuid4()
    run.created_at = datetime.now(UTC)
    run.updated_at = datetime.now(UTC)
    run.judge_status = GitHubReviewJudgeStatus.not_applicable
    run.judge_escalation_candidate_count = 0
    response = GitHubReviewRunResponse.model_validate(run)
    assert response.judge_status == GitHubReviewJudgeStatus.not_applicable
    assert response.judge_escalation_candidate_count == 0
    assert response.context_stats is None


def test_review_run_response_includes_context_stats():
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
    )
    run.id = uuid.uuid4()
    run.created_at = datetime.now(UTC)
    run.updated_at = datetime.now(UTC)
    run.judge_status = GitHubReviewJudgeStatus.not_applicable
    run.judge_escalation_candidate_count = 0
    run.context_stats = {
        "active_program": "review-engineering-context",
        "diff_max_bytes": 524288,
        "unified_diff_bytes": 120000,
        "diff_truncated": False,
        "omitted_files_count": 0,
        "omitted_md_count": 0,
        "engineering_context_injected": True,
        "engineering_context_bytes": 4096,
        "engineering_context_deduped_paths": [],
        "lock_ids_extracted": ["RCX-D8"],
        "engineering_context_errors": [],
        "prompt_chars": 150000,
    }
    response = GitHubReviewRunResponse.model_validate(run)
    assert response.context_stats is not None
    assert response.context_stats["engineering_context_injected"] is True
    assert response.context_stats["lock_ids_extracted"] == ["RCX-D8"]


def test_finding_polish_defaults():
    finding = GitHubFindingORM(
        review_run_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="Details",
    )
    assert finding.suggestion is None
