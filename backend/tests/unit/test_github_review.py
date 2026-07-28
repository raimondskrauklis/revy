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


def test_normalize_finding_start_line():
    assert github_review.normalize_finding_start_line(12) == 12
    assert github_review.normalize_finding_start_line("15") == 15
    assert github_review.normalize_finding_start_line(0) is None
    assert github_review.normalize_finding_start_line("abc") is None


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
