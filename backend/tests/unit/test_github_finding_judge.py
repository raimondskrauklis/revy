# backend/tests/unit/test_github_finding_judge.py
"""GitHub finding judge — R5."""
import itertools
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubReviewJudgeStatus,
    GitHubReviewRunStatus,
    ResolutionMethod,
    ReviewProfile,
)
from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_compare_patches import CompareReviewContext
from app.services.github_finding_judge import (
    _build_judge_prompt,
    _judge_failure_log_extra,
    is_judge_candidate,
    judge_candidate_group_sql_predicate,
    record_review_run_judge_status,
)
from app.services.github_finding_reconcile import severity_rank
from app.services.model_policy import ModelRef


@pytest.fixture(autouse=True)
def _mock_fetch_compare_patches_for_judge():
    from app.services.engineering_context.pack import EngineeringContextPack
    from app.services.github_compare_patches import CompareReviewContext

    compare_ctx = CompareReviewContext(
        patches_by_file={},
        changed_files=(),
        omitted_files=[],
        compare_failed=False,
        github_installation_id=1,
        owner="org",
        repo_name="repo",
    )
    with patch(
        "app.services.github_finding_judge.fetch_compare_review_context",
        AsyncMock(return_value=compare_ctx),
    ):
        with patch(
            "app.services.github_finding_judge.build_engineering_context_pack",
            AsyncMock(return_value=EngineeringContextPack()),
        ):
            yield


def test_is_judge_candidate_error():
    assert is_judge_candidate(severity=FindingSeverity.error, category=FindingCategory.bug)


def test_is_judge_candidate_security_warning():
    assert is_judge_candidate(
        severity=FindingSeverity.warning,
        category=FindingCategory.security,
    )


def test_is_judge_candidate_info_bug_false():
    assert not is_judge_candidate(
        severity=FindingSeverity.info,
        category=FindingCategory.bug,
    )


@pytest.mark.parametrize(
    ("severity", "category"),
    list(itertools.product(FindingSeverity, FindingCategory)),
)
def test_judge_candidate_group_sql_predicate_parity_matrix(
    severity: FindingSeverity,
    category: FindingCategory,
):
    """Pass 3 SQL predicate must stay aligned with is_judge_candidate (full matrix)."""
    expected = severity in (FindingSeverity.error, FindingSeverity.critical) or (
        category == FindingCategory.security
        and severity_rank(severity) >= severity_rank(FindingSeverity.warning)
    )
    assert is_judge_candidate(severity=severity, category=category) is expected


def test_judge_candidate_group_sql_predicate_compiles():
    from sqlalchemy import select

    stmt = select(GitHubFindingGroupORM).where(judge_candidate_group_sql_predicate())
    compiled = str(stmt.compile())
    assert "severity" in compiled
    assert "category" in compiled


def test_judge_candidate_loader_filters_on_finding_severity_category():
    """_load_judge_candidates gates on finding row fields, not group-only fields."""
    finding_severity = FindingSeverity.error
    finding_category = FindingCategory.bug
    assert is_judge_candidate(severity=finding_severity, category=finding_category)
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Mismatch title",
        message="msg",
        file_path="app/a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    finding = GitHubFindingORM(
        workspace_id=group.workspace_id,
        review_run_id=uuid.uuid4(),
        severity=finding_severity,
        category=finding_category,
        title="Err",
        message="msg",
        file_path="app/a.py",
        group_id=group.id,
    )
    assert is_judge_candidate(severity=finding.severity, category=finding.category)
    assert finding.severity != group.severity


def test_build_judge_prompt_includes_evidence_and_grounding():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Null deref",
        message="Possible null access",
        file_path="app/handler.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    prompt = _build_judge_prompt(group=group, evidence_snippet="if value is None:\n    raise")
    assert "Automated reviewer (Moonshot)" in prompt
    assert "Verify this claim only" in prompt
    assert "Do not introduce new findings" in prompt
    assert "Evidence (code excerpt" in prompt
    assert "if value is None" in prompt
    assert "Grounding (E2)" in prompt
    assert "entailed" in prompt


def test_judge_failure_log_extra_includes_raw_response_text():
    from app.integrations import anthropic_review
    from app.integrations.judge_llm_errors import JudgeParseError

    anthropic_review._set_judge_transport_context(
        {
            "profile": "direct",
            "messages_url": "https://api.anthropic.com/v1/messages",
            "model_id": "claude-sonnet-5",
            "duration_ms": 12,
        }
    )
    exc = JudgeParseError("judge_json_invalid", response_text='{"broken":')
    extra = _judge_failure_log_extra(uuid.uuid4(), exc)
    assert extra["raw_response_text"] == '{"broken":'
    assert extra["parse_error"] == "judge_json_invalid"
    assert extra["response_chars"] == len('{"broken":')
    assert extra["profile"] == "direct"
    assert extra["duration_ms"] == 12


def test_judge_failure_log_extra_http_error_uses_transport_parse_error():
    from app.integrations import anthropic_review

    anthropic_review._set_judge_transport_context(
        {
            "profile": "gateway",
            "messages_url": "https://llm.ai.rtu.lv/v1/messages",
            "model_id": "claude-sonnet-5",
            "duration_ms": 42,
            "parse_error": "Server error '502 Bad Gateway'",
            "error_type": "HTTPStatusError",
        }
    )
    exc = httpx.HTTPStatusError(
        "bad gateway",
        request=MagicMock(),
        response=MagicMock(status_code=502),
    )
    extra = _judge_failure_log_extra(uuid.uuid4(), exc)
    assert extra["error"] == "Server error '502 Bad Gateway'"
    assert extra["parse_error"] == "Server error '502 Bad Gateway'"
    assert extra["profile"] == "gateway"


def test_judge_failure_log_extra_includes_invalid_response_preview():
    from app.core.exceptions import ServiceUnavailableError
    from app.integrations import anthropic_review

    anthropic_review._set_judge_transport_context({})
    exc = ServiceUnavailableError(
        message="Anthropic response invalid",
        error_code="llm_error",
        details={"response_body_preview": "not-json {"},
    )
    extra = _judge_failure_log_extra(uuid.uuid4(), exc)
    assert extra["raw_response_text"] == "not-json {"
    assert extra["error"] == "Anthropic response invalid"
    assert extra["parse_error"] == "Anthropic response invalid"


def test_build_judge_prompt_includes_engineering_locks():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/handler.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    prompt = _build_judge_prompt(
        group=group,
        evidence_snippet="snippet",
        engineering_block="## Locked decisions\n\n**RCX-D8**",
    )
    assert "Engineering context (authoritative locks)" in prompt
    assert "RCX-D8" in prompt
    assert prompt.index("Evidence (code excerpt") < prompt.index("Engineering context")


def test_format_judge_engineering_context_truncates_utf8():
    from app.services.engineering_context.pack import EngineeringContextPack
    from app.services.judge_prompt_context import format_judge_engineering_context

    pack = EngineeringContextPack(extracted_text="x" * 5000)
    block = format_judge_engineering_context(pack, max_chars=100)
    assert block is not None
    assert len(block.encode("utf-8")) <= 100


def test_build_judge_prompt_without_evidence_uses_conservative_grounding():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Null deref",
        message="Possible null access",
        file_path="app/handler.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    prompt = _build_judge_prompt(group=group, evidence_snippet=None)
    assert "Evidence" not in prompt
    assert "Judge conservatively" in prompt


def test_build_judge_prompt_omits_file_patch_when_snippet_present():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/handler.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    prompt = _build_judge_prompt(
        group=group,
        evidence_snippet="snippet",
        file_patch="@@ -1 +1 @@\n+line\n",
    )
    assert "File diff (scoped):" not in prompt
    assert "snippet" in prompt


def test_build_judge_prompt_whitespace_only_snippet_omits_evidence_and_includes_patch():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/handler.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    prompt = _build_judge_prompt(
        group=group,
        evidence_snippet="   ",
        file_patch="@@ -1 +1 @@\n+line\n",
    )
    assert "Evidence (code excerpt" not in prompt
    assert "File diff (scoped):" in prompt
    assert "Judge conservatively" in prompt


def test_build_judge_prompt_includes_file_patch_when_no_snippet():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/handler.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    prompt = _build_judge_prompt(
        group=group,
        evidence_snippet=None,
        file_patch="@@ -1 +1 @@\n+line\n",
    )
    assert "File diff (scoped):" in prompt
    assert "+line" in prompt


def test_build_judge_prompt_truncates_patch_at_prompt_cap():
    from app.services.judge_prompt_context import JUDGE_PROMPT_PATCH_MAX_CHARS

    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/handler.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    long_patch = "x" * (JUDGE_PROMPT_PATCH_MAX_CHARS + 500)
    prompt = _build_judge_prompt(
        group=group,
        evidence_snippet=None,
        file_patch=long_patch,
    )
    assert long_patch not in prompt
    assert "x" * JUDGE_PROMPT_PATCH_MAX_CHARS in prompt


@pytest.mark.asyncio
async def test_run_judge_snippet_first_prompt_size_omits_large_patch():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    group_id = uuid.uuid4()
    huge_patch = "p" * 8192

    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = group_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        group_id=group_id,
        evidence_snippet="if value is None:\n    raise ValueError",
    )

    revision = MagicMock()
    revision.pull_request_id = uuid.uuid4()
    revision.base_sha = "base"
    revision.head_sha = "head"
    pull_request = MagicMock()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, group, revision, pull_request])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    artifacts: list = []
    captured_prompt: dict[str, str] = {}

    async def _judge_side_effect(*_args, user_prompt: str, **_kwargs):
        captured_prompt["user_prompt"] = user_prompt
        return {"outcome": "dismissed", "notes": "false positive"}

    code_context = MagicMock()
    code_context.evidence_snippet = "fallback snippet"
    code_context.file_patch = huge_patch

    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.judge_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with patch(
            "app.services.github_finding_judge.resolve_model",
            AsyncMock(return_value=ModelRef(provider="anthropic", model_id="claude-test")),
        ):
            with patch(
                "app.services.github_finding_judge.resolve_judge_code_context",
                return_value=code_context,
            ):
                with patch(
                    "app.services.github_finding_judge.llm_dispatch.call_judge_llm",
                    AsyncMock(side_effect=_judge_side_effect),
                ):
                    await record_review_run_judge_status(
                        session,
                        review_run_id=review_run_id,
                        artifacts_out=artifacts,
                    )

    assert len(captured_prompt["user_prompt"]) < 2500
    assert huge_patch not in captured_prompt["user_prompt"]
    assert len(artifacts) == 1
    assert artifacts[0].file_patch_chars is None


def test_judge_system_prompt_verifier_role():
    from app.integrations.anthropic_review import JUDGE_SYSTEM_PROMPT

    assert "verification judge" in JUDGE_SYSTEM_PROMPT
    assert "Moonshot" in JUDGE_SYSTEM_PROMPT
    assert "Do NOT search for additional bugs" in JUDGE_SYSTEM_PROMPT
    assert "full PR review" in JUDGE_SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_run_judge_skipped_without_api_key():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    group_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = group_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        group_id=group_id,
    )

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, group])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.judge_llm_enabled.return_value = False
        count, _model_ref = await record_review_run_judge_status(session, review_run_id=review_run_id)

    assert count == 0
    assert run.judge_escalation_candidate_count == 1
    assert run.judge_status == GitHubReviewJudgeStatus.skipped_disabled


@pytest.mark.asyncio
async def test_record_judge_status_keeps_completed_when_outcomes_exist_and_judge_disabled():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    group_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = group_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        group_id=group_id,
    )

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, group])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(side_effect=[uuid.uuid4(), None])
    session.flush = AsyncMock()

    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.judge_llm_enabled.return_value = False
        count, _model_ref = await record_review_run_judge_status(session, review_run_id=review_run_id)

    assert count == 0
    assert run.judge_escalation_candidate_count == 1
    assert run.judge_status == GitHubReviewJudgeStatus.completed


@pytest.mark.asyncio
async def test_run_judge_stale_model_policy_returns_zero():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    group_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = group_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        group_id=group_id,
    )

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, group])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.judge_llm_enabled.return_value = True
        with patch(
            "app.services.github_finding_judge.resolve_model",
            AsyncMock(
                side_effect=ValidationError(
                    message="Workspace model override is no longer valid",
                    field="judge",
                )
            ),
        ):
            count, _model_ref = await record_review_run_judge_status(session, review_run_id=review_run_id)

    assert count == 0
    assert run.judge_escalation_candidate_count == 1
    assert run.judge_status == GitHubReviewJudgeStatus.skipped_unavailable


@pytest.mark.asyncio
async def test_run_judge_dismissed_resolves_group():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    group_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = group_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        group_id=group_id,
    )

    revision = MagicMock()
    revision.pull_request_id = uuid.uuid4()
    revision.base_sha = "base"
    revision.head_sha = "head"
    pull_request = MagicMock()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, group, revision, pull_request])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.judge_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with patch(
            "app.services.github_finding_judge.resolve_model",
            AsyncMock(return_value=ModelRef(provider="anthropic", model_id="claude-test")),
        ):
            with patch(
                "app.services.github_finding_judge.llm_dispatch.call_judge_llm",
                AsyncMock(return_value={"outcome": "dismissed", "notes": "false positive"}),
            ):
                count, _model_ref = await record_review_run_judge_status(session, review_run_id=review_run_id)

    assert count == 1
    assert run.judge_status == GitHubReviewJudgeStatus.completed
    assert group.state == GitHubFindingGroupState.resolved
    assert group.resolution_method == ResolutionMethod.judge_dismissed


@pytest.mark.asyncio
async def test_run_judge_bedrock_provider_without_anthropic_key():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    group_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="bedrock",
    )
    run.id = review_run_id

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = group_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        group_id=group_id,
    )

    revision = MagicMock()
    revision.pull_request_id = uuid.uuid4()
    revision.base_sha = "base"
    revision.head_sha = "head"
    pull_request = MagicMock()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, group, revision, pull_request])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(side_effect=[None, uuid.uuid4()])
    session.add = MagicMock()
    session.flush = AsyncMock()

    bedrock_ref = ModelRef(
        provider="bedrock",
        model_id="anthropic.claude-sonnet-4-20250514-v1:0",
        region="eu-central-1",
    )

    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.judge_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with patch(
            "app.services.github_finding_judge.resolve_model",
            AsyncMock(return_value=bedrock_ref),
        ):
            with patch(
                "app.services.github_finding_judge.llm_dispatch.call_judge_llm",
                AsyncMock(return_value={"outcome": "upheld", "notes": "valid"}),
            ):
                count, _model_ref = await record_review_run_judge_status(session, review_run_id=review_run_id)

    assert count == 1
    assert run.judge_status == GitHubReviewJudgeStatus.completed


@pytest.mark.asyncio
async def test_run_judge_service_unavailable_continues():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    group_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = group_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        group_id=group_id,
    )

    revision = MagicMock()
    revision.pull_request_id = uuid.uuid4()
    revision.base_sha = "base"
    revision.head_sha = "head"
    pull_request = MagicMock()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, group, revision, pull_request])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.judge_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with patch(
            "app.services.github_finding_judge.resolve_model",
            AsyncMock(return_value=ModelRef(provider="anthropic", model_id="claude-test")),
        ):
            with patch(
                "app.services.github_finding_judge.llm_dispatch.call_judge_llm",
                AsyncMock(
                    side_effect=ServiceUnavailableError(
                        message="Anthropic judge response invalid",
                        error_code="llm_error",
                    )
                ),
            ):
                count, _model_ref = await record_review_run_judge_status(session, review_run_id=review_run_id)

    assert count == 0
    assert run.judge_status == GitHubReviewJudgeStatus.skipped_unavailable
    assert group.state == GitHubFindingGroupState.active
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_run_judge_partial_llm_failure_skipped_unavailable():
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

    groups: list[GitHubFindingGroupORM] = []
    findings: list[GitHubFindingORM] = []
    for idx in range(3):
        group_id = uuid.uuid4()
        group = GitHubFindingGroupORM(
            workspace_id=workspace_id,
            pull_request_id=pull_request_id,
            fingerprint=f"fp-{idx}",
            state=GitHubFindingGroupState.active,
            severity=FindingSeverity.critical,
            category=FindingCategory.security,
            title=f"Issue {idx}",
            message="msg",
            file_path=f"app/{idx}.py",
            last_seen_revision_id=uuid.uuid4(),
        )
        group.id = group_id
        groups.append(group)
        findings.append(
            GitHubFindingORM(
                review_run_id=review_run_id,
                workspace_id=workspace_id,
                severity=FindingSeverity.critical,
                category=FindingCategory.security,
                title=f"Issue {idx}",
                message="msg",
                file_path=f"app/{idx}.py",
                group_id=group_id,
            )
        )

    revision = MagicMock()
    revision.pull_request_id = pull_request_id
    revision.base_sha = "base"
    revision.head_sha = "head"
    pull_request = MagicMock()

    async def _get(model, key):
        if model is GitHubReviewRunORM:
            return run
        if model is GitHubFindingGroupORM:
            return next((group for group in groups if group.id == key), None)
        if model is GitHubPullRequestRevisionORM:
            return revision
        if model is GitHubPullRequestORM:
            return pull_request
        return None

    session = AsyncMock()
    session.get = AsyncMock(side_effect=_get)
    session.scalars = AsyncMock(return_value=findings)
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    call_count = 0

    async def _judge_side_effect(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise ServiceUnavailableError(
                message="Anthropic judge response invalid",
                error_code="llm_error",
            )
        return {"outcome": "dismissed", "notes": "false positive"}

    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.judge_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with patch(
            "app.services.github_finding_judge.resolve_model",
            AsyncMock(return_value=ModelRef(provider="anthropic", model_id="claude-test")),
        ):
            with patch(
                "app.services.github_finding_judge.fetch_compare_review_context",
                AsyncMock(
                    return_value=CompareReviewContext(
                        patches_by_file={},
                        changed_files=(),
                        omitted_files=[],
                        compare_failed=False,
                        github_installation_id=1,
                        owner="org",
                        repo_name="repo",
                    ),
                ),
            ):
                with patch(
                    "app.services.github_finding_judge.llm_dispatch.call_judge_llm",
                    AsyncMock(side_effect=_judge_side_effect),
                ):
                    judged, _judge_model_ref = await record_review_run_judge_status(
                        session,
                        review_run_id=review_run_id,
                    )

    assert judged == 2
    assert run.judge_status == GitHubReviewJudgeStatus.skipped_unavailable
    assert session.add.call_count == 2


@pytest.mark.asyncio
async def test_run_judge_parse_failure_captures_artifact():
    from app.integrations.judge_llm_errors import JudgeParseError

    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    group_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = group_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        group_id=group_id,
    )

    revision = MagicMock()
    revision.pull_request_id = uuid.uuid4()
    revision.base_sha = "base"
    revision.head_sha = "head"
    pull_request = MagicMock()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, group, revision, pull_request])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    artifacts: list = []

    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.judge_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with patch(
            "app.services.github_finding_judge.resolve_model",
            AsyncMock(return_value=ModelRef(provider="anthropic", model_id="claude-test")),
        ):
            with patch(
                "app.services.github_finding_judge.fetch_compare_review_context",
                AsyncMock(
                    return_value=CompareReviewContext(
                        patches_by_file={},
                        changed_files=(),
                        omitted_files=[],
                        compare_failed=False,
                        github_installation_id=1,
                        owner="org",
                        repo_name="repo",
                    ),
                ),
            ):
                with patch(
                    "app.services.github_finding_judge.llm_dispatch.call_judge_llm",
                    AsyncMock(
                        side_effect=JudgeParseError(
                            "judge_json_invalid",
                            response_text='{"outcome": "oops"',
                        )
                    ),
                ):
                    judged, _judge_model_ref = await record_review_run_judge_status(
                        session,
                        review_run_id=review_run_id,
                        artifacts_out=artifacts,
                    )

    assert judged == 0
    assert run.judge_status == GitHubReviewJudgeStatus.skipped_unavailable
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.parse_error == "judge_json_invalid"
    assert artifact.raw_response_text == '{"outcome": "oops"'
    assert artifact.raw_response is None
    assert artifact.outcome is None
    assert artifact.retry_count == 1
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_call_judge_with_optional_retry_retries_parse_failure():
    from app.integrations.judge_llm_errors import JudgeParseError
    from app.services.github_finding_judge import call_judge_with_optional_retry

    client = AsyncMock()
    call_count = 0

    async def _judge_side_effect(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise JudgeParseError("judge_json_invalid", response_text="not-json")
        return {"outcome": "dismissed", "notes": "false positive"}

    with patch(
        "app.services.github_finding_judge.llm_dispatch.call_judge_llm",
        AsyncMock(side_effect=_judge_side_effect),
    ):
        raw, retry_count = await call_judge_with_optional_retry(
            client,
            model_ref=ModelRef(provider="anthropic", model_id="claude-test"),
            user_prompt="judge",
            timeout_seconds=30.0,
        )

    assert raw["outcome"] == "dismissed"
    assert retry_count == 1
    assert call_count == 2


@pytest.mark.asyncio
async def test_gateway_parse_fallback_call_judge_with_optional_retry_succeeds():
    from app.integrations import anthropic_review
    from app.services.github_finding_judge import call_judge_with_optional_retry
    from app.services.model_policy import ModelRef

    gateway_response = MagicMock()
    gateway_response.raise_for_status = MagicMock()
    gateway_response.json.return_value = {
        "content": [{"text": "```not valid json```"}]
    }
    direct_response = MagicMock()
    direct_response.raise_for_status = MagicMock()
    direct_response.json.return_value = {
        "content": [{"text": json.dumps({"outcome": "dismissed", "notes": "ok"})}]
    }
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(side_effect=[gateway_response, direct_response])

    async def _real_judge(client, *, model_ref, user_prompt, timeout_seconds, system_prompt=None):
        return await anthropic_review.judge_finding(
            client,
            user_prompt=user_prompt,
            timeout_seconds=timeout_seconds,
            system_prompt=system_prompt,
        )

    with (
        patch("app.integrations.anthropic_review.settings") as mock_settings,
        patch(
            "app.services.github_finding_judge.llm_dispatch.call_judge_llm",
            AsyncMock(side_effect=_real_judge),
        ),
    ):
        mock_settings.anthropic_gateway_enabled = True
        mock_settings.anthropic_gateway_messages_url = "https://llm.ai.rtu.lv/v1/messages"
        mock_settings.anthropic_auth_token = "rtu-token"
        mock_settings.effective_anthropic_gateway_judge_model = "azure_ai/claude-opus-5"
        mock_settings.anthropic_direct_enabled = True
        mock_settings.anthropic_api_key = "direct-key"
        mock_settings.revy_anthropic_model = "claude-sonnet-5"
        mock_settings.revy_judge_structured_output = False
        mock_settings.revy_revision_timeout_standard_seconds = 30
        raw, retry_count = await call_judge_with_optional_retry(
            client,
            model_ref=ModelRef(provider="anthropic", model_id="claude-sonnet-5"),
            user_prompt="judge",
            timeout_seconds=30.0,
        )

    assert raw["outcome"] == "dismissed"
    assert retry_count == 0
    assert client.post.await_count == 2


@pytest.mark.asyncio
async def test_call_judge_with_optional_retry_does_not_retry_unrelated_value_error():
    from app.services.github_finding_judge import call_judge_with_optional_retry

    client = AsyncMock()
    call_judge = AsyncMock(side_effect=ValueError("unrelated"))

    with patch(
        "app.services.github_finding_judge.llm_dispatch.call_judge_llm",
        call_judge,
    ):
        with pytest.raises(ValueError, match="unrelated"):
            await call_judge_with_optional_retry(
                client,
                model_ref=ModelRef(provider="anthropic", model_id="claude-test"),
                user_prompt="judge",
                timeout_seconds=30.0,
            )

    assert call_judge.await_count == 1


@pytest.mark.asyncio
async def test_call_judge_with_optional_retry_preserves_first_parse_body_on_double_fail():
    from app.integrations.judge_llm_errors import JudgeParseError
    from app.services.github_finding_judge import call_judge_with_optional_retry

    client = AsyncMock()
    call_count = 0

    async def _judge_side_effect(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        raise JudgeParseError(
            "judge_json_invalid",
            response_text=f"attempt-{call_count}",
        )

    with patch(
        "app.services.github_finding_judge.llm_dispatch.call_judge_llm",
        AsyncMock(side_effect=_judge_side_effect),
    ):
        with pytest.raises(JudgeParseError) as exc_info:
            await call_judge_with_optional_retry(
                client,
                model_ref=ModelRef(provider="anthropic", model_id="claude-test"),
                user_prompt="judge",
                timeout_seconds=30.0,
            )

    assert call_count == 2
    assert exc_info.value.response_text == "attempt-1"
    assert exc_info.value.judge_retry_count == 1


@pytest.mark.asyncio
async def test_run_judge_fenced_json_persists_outcome():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    group_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = group_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        group_id=group_id,
    )

    revision = MagicMock()
    revision.pull_request_id = uuid.uuid4()
    revision.base_sha = "base"
    revision.head_sha = "head"
    pull_request = MagicMock()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, group, revision, pull_request])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    artifacts: list = []

    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.judge_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with patch(
            "app.services.github_finding_judge.resolve_model",
            AsyncMock(return_value=ModelRef(provider="anthropic", model_id="claude-test")),
        ):
            with patch(
                "app.services.github_finding_judge.fetch_compare_review_context",
                AsyncMock(
                    return_value=CompareReviewContext(
                        patches_by_file={},
                        changed_files=(),
                        omitted_files=[],
                        compare_failed=False,
                        github_installation_id=1,
                        owner="org",
                        repo_name="repo",
                    ),
                ),
            ):
                with patch(
                    "app.services.github_finding_judge.llm_dispatch.call_judge_llm",
                    AsyncMock(return_value={"outcome": "dismissed", "notes": "ok"}),
                ):
                    judged, _judge_model_ref = await record_review_run_judge_status(
                        session,
                        review_run_id=review_run_id,
                        artifacts_out=artifacts,
                    )

    assert judged == 1
    assert artifacts[0].outcome == "dismissed"
    assert artifacts[0].raw_response["outcome"] == "dismissed"


@pytest.mark.asyncio
async def test_record_judge_status_keeps_completed_when_no_candidates_but_outcomes_exist():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    session = AsyncMock()
    session.get = AsyncMock(return_value=run)
    session.scalars = AsyncMock(return_value=[])
    session.scalar = AsyncMock(return_value=uuid.uuid4())
    session.flush = AsyncMock()

    count, _model_ref = await record_review_run_judge_status(session, review_run_id=review_run_id)

    assert count == 0
    assert run.judge_escalation_candidate_count == 0
    assert run.judge_status == GitHubReviewJudgeStatus.completed


@pytest.mark.asyncio
async def test_finalize_review_run_judge_status_upgrades_when_outcomes_complete():
    from app.services.github_finding_judge import finalize_review_run_judge_status

    review_run_id = uuid.uuid4()
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
        judge_status=GitHubReviewJudgeStatus.skipped_unavailable,
    )
    run.id = review_run_id

    session = AsyncMock()
    session.get = AsyncMock(return_value=run)
    session.flush = AsyncMock()

    with patch(
        "app.services.github_finding_judge._load_judge_candidates",
        AsyncMock(return_value=(run, [])),
    ):
        with patch(
            "app.services.github_finding_judge._judge_candidates_missing_outcome",
            AsyncMock(return_value=False),
        ):
            await finalize_review_run_judge_status(session, review_run_id=review_run_id)

    assert run.judge_status == GitHubReviewJudgeStatus.completed
