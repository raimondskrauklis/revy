# backend/tests/unit/test_github_finding_judge.py
"""GitHub finding judge — R5."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

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
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_finding_judge import (
    _build_judge_prompt,
    is_judge_candidate,
    record_review_run_judge_status,
)
from app.services.model_policy import ModelRef


@pytest.fixture(autouse=True)
def _mock_fetch_compare_patches_for_judge():
    with patch(
        "app.services.github_finding_judge.fetch_compare_patches_by_file",
        AsyncMock(return_value={}),
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


def test_build_judge_prompt_includes_file_patch():
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
    assert "File diff (scoped):" in prompt
    assert "+line" in prompt


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
        count = await record_review_run_judge_status(session, review_run_id=review_run_id)

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
        count = await record_review_run_judge_status(session, review_run_id=review_run_id)

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
            count = await record_review_run_judge_status(session, review_run_id=review_run_id)

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
                count = await record_review_run_judge_status(session, review_run_id=review_run_id)

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
                count = await record_review_run_judge_status(session, review_run_id=review_run_id)

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
                count = await record_review_run_judge_status(session, review_run_id=review_run_id)

    assert count == 0
    assert run.judge_status == GitHubReviewJudgeStatus.skipped_unavailable
    assert group.state == GitHubFindingGroupState.active
    session.add.assert_not_called()


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

    count = await record_review_run_judge_status(session, review_run_id=review_run_id)

    assert count == 0
    assert run.judge_escalation_candidate_count == 0
    assert run.judge_status == GitHubReviewJudgeStatus.completed
