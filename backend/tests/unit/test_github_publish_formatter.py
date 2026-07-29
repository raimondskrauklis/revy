# backend/tests/unit/test_github_publish_formatter.py
"""GitHub publish formatter — RQ7."""
import uuid
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubIndexMode,
    ResolutionMethod,
    ResolutionStatus,
)
from app.models.github_finding_group import GitHubFindingGroupORM
from app.services.github_publish_formatter import (
    PublishFormatContext,
    build_check_run_summary,
    build_g9_resolution_prose,
    build_pr_review_comment_fallback,
    build_publish_format_result,
    compute_confidence,
    count_resolution_status,
    format_resolution_metrics_block,
    format_summary_comment,
    normalize_llm_issue_comment,
)


def _group(*, state=GitHubFindingGroupState.active, severity=FindingSeverity.warning, **kwargs):
    defaults = {
        "workspace_id": uuid.uuid4(),
        "pull_request_id": uuid.uuid4(),
        "fingerprint": "fp",
        "state": state,
        "severity": severity,
        "category": FindingCategory.bug,
        "title": "Issue",
        "message": "Details",
        "file_path": "app/main.py",
        "last_seen_revision_id": uuid.uuid4(),
    }
    defaults.update(kwargs)
    return GitHubFindingGroupORM(**defaults)


def _ctx(groups: list[GitHubFindingGroupORM]) -> PublishFormatContext:
    return PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=groups,
    )


def test_compute_confidence_five_when_no_active_findings():
    resolved = _group(state=GitHubFindingGroupState.resolved)
    assert compute_confidence([resolved]) == 5


def test_compute_confidence_lower_for_errors():
    assert compute_confidence([_group(severity=FindingSeverity.error)]) <= 3


def test_compute_confidence_ceiling_with_warnings_and_resolution_bonus():
    groups = [
        _group(severity=FindingSeverity.warning, fingerprint="w"),
        _group(
            resolution_method=ResolutionMethod.absent_and_addressed,
            state=GitHubFindingGroupState.resolved,
            fingerprint="r",
        ),
        _group(
            resolution_method=ResolutionMethod.judge_dismissed,
            state=GitHubFindingGroupState.resolved,
            fingerprint="j",
        ),
    ]
    assert compute_confidence(groups) <= 4


def test_confidence_rationale_four_without_resolution_omits_progress_claim():
    from app.services.github_publish_formatter import _confidence_rationale

    groups = [_group(severity=FindingSeverity.warning, fingerprint="w")]
    rationale = _confidence_rationale(groups)
    assert "Prior fixes" not in rationale
    assert "some active findings remain" in rationale


def test_build_g9_resolution_prose_ignores_addressed_still_active():
    groups = [
        _group(
            resolution_status=ResolutionStatus.addressed,
            state=GitHubFindingGroupState.active,
        ),
    ]
    assert build_g9_resolution_prose(groups) == ""


def test_build_g9_resolution_prose():
    groups = [
        _group(
            resolution_method=ResolutionMethod.absent_and_addressed,
            state=GitHubFindingGroupState.resolved,
            fingerprint="a",
        ),
        _group(
            resolution_method=ResolutionMethod.judge_dismissed,
            state=GitHubFindingGroupState.resolved,
            fingerprint="b",
        ),
    ]
    prose = build_g9_resolution_prose(groups)
    assert "fixed since last push" in prose
    assert "dismissed by judge" in prose


def test_count_resolution_status_uses_resolution_method():
    groups = [
        _group(
            resolution_method=ResolutionMethod.absent_and_addressed,
            state=GitHubFindingGroupState.resolved,
            fingerprint="a",
        ),
        _group(
            resolution_method=ResolutionMethod.verification_dismissed,
            state=GitHubFindingGroupState.resolved,
            fingerprint="b",
        ),
        _group(
            resolution_status=ResolutionStatus.still_open,
            state=GitHubFindingGroupState.active,
            fingerprint="c",
        ),
    ]
    counts = count_resolution_status(groups)
    assert counts[ResolutionStatus.addressed.value] == 1
    assert counts[ResolutionMethod.verification_dismissed.value] == 1
    assert counts[ResolutionStatus.still_open.value] == 1


def test_format_resolution_metrics_block():
    block = format_resolution_metrics_block(
        {
            "resolution_rate_pct": 50.0,
            "transition_count": 1,
            "denominator_active_prior": 2,
            "transitions_addressed": 1,
            "transitions_dismissed": {"judge_dismissed": 0, "verification_dismissed": 0},
            "still_open_count": 1,
            "compare_failed_count": 0,
        }
    )
    assert "Resolution rate" in block
    assert "Closed as fixed" in block
    assert "Still open" in block


def test_build_pr_review_comment_fallback_includes_resolution_metrics_block():
    groups = [
        _group(
            resolution_method=ResolutionMethod.absent_and_addressed,
            state=GitHubFindingGroupState.resolved,
        ),
    ]
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=groups,
        resolution_metrics_manifest={
            "resolution_rate_pct": 100.0,
            "transition_count": 1,
            "denominator_active_prior": 1,
            "transitions_addressed": 1,
            "transitions_dismissed": {},
            "compare_failed_count": 0,
        },
    )
    markdown = build_pr_review_comment_fallback(ctx)
    assert "Resolution metrics (this push)" in markdown


def test_build_check_run_summary_two_block():
    generation = [_group(severity=FindingSeverity.error, fingerprint="gen")]
    prior_only = _group(
        severity=FindingSeverity.warning,
        fingerprint="prior",
        file_path="app/legacy.py",
    )
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=generation,
        pr_active_groups=[*generation, prior_only],
    )
    markdown = build_check_run_summary(ctx)
    assert "**Confidence:**" in markdown
    assert "### This generation" in markdown
    assert "### Still open on PR" in markdown
    assert "app/legacy.py" in markdown


def test_format_summary_comment_two_block():
    generation = [_group(severity=FindingSeverity.error, fingerprint="gen")]
    prior_only = _group(severity=FindingSeverity.warning, fingerprint="prior")
    markdown = format_summary_comment(
        generation_groups=generation,
        pr_active_groups=[*generation, prior_only],
    )
    assert "### This generation" in markdown
    assert "### Still open on PR" in markdown


def test_build_pr_review_comment_fallback_generation_only_not_pr_block():
    generation = [_group(severity=FindingSeverity.error, fingerprint="gen")]
    prior_only = _group(
        severity=FindingSeverity.warning,
        fingerprint="prior",
        file_path="app/legacy.py",
    )
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=generation,
        pr_active_groups=[*generation, prior_only],
    )
    markdown = build_pr_review_comment_fallback(ctx)
    assert "app/legacy.py" not in markdown
    assert "### Still open on PR" not in markdown


def test_build_check_run_summary_is_compact():
    markdown = build_check_run_summary(_ctx([_group(severity=FindingSeverity.error)]))
    assert "**Confidence:**" in markdown
    assert "Since last push" not in markdown
    assert "| error |" in markdown or "FindingSeverity.error" in markdown


def test_build_pr_review_comment_fallback_includes_g9_and_metadata():
    groups = [
        _group(
            resolution_method=ResolutionMethod.absent_and_addressed,
            state=GitHubFindingGroupState.resolved,
        ),
    ]
    markdown = build_pr_review_comment_fallback(_ctx(groups))
    assert "Confidence score" in markdown
    assert "Since last push" in markdown
    assert "<details>" in markdown
    assert "Open in Revy" in markdown


def test_normalize_llm_issue_comment_unwraps_json_body():
    wrapped = (
        '{"body":"## Revy code review\\n\\n**Confidence score:** 4/5\\n\\n### Findings"}'
    )
    assert normalize_llm_issue_comment(wrapped).startswith("## Revy code review")
    assert "Confidence score" in normalize_llm_issue_comment(wrapped)


def test_normalize_llm_issue_comment_unwraps_review_comment_key():
    wrapped = '{"review_comment":"## Pull Request Review\\n\\nNarrative here."}'
    assert normalize_llm_issue_comment(wrapped) == "## Pull Request Review\n\nNarrative here."


def test_normalize_llm_issue_comment_unknown_json_returns_none():
    assert normalize_llm_issue_comment('{"findings":[]}') is None


def test_looks_like_json_wrapper_only_known_keys():
    from app.services.github_publish_formatter import _looks_like_json_wrapper

    assert _looks_like_json_wrapper('{"review_comment":"## Hi"}') is True
    assert _looks_like_json_wrapper('{"findings":[]}') is False
    assert _looks_like_json_wrapper("## plain markdown") is False


def test_normalize_llm_issue_comment_passes_through_markdown():
    markdown = "## Revy code review\n\nplain markdown"
    assert normalize_llm_issue_comment(markdown) == markdown


@pytest.mark.asyncio
async def test_build_pr_review_comment_unwraps_json_body_from_moonshot():
    from app.services.github_publish_formatter import build_pr_review_comment

    groups = [_group(severity=FindingSeverity.warning)]
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=groups,
        resolution_metrics_manifest={
            "resolution_rate_pct": 100.0,
            "transition_count": 1,
            "denominator_active_prior": 1,
            "transitions_addressed": 1,
            "transitions_dismissed": {},
            "compare_failed_count": 0,
            "still_open_count": 0,
        },
    )
    moonshot_json = (
        '{"body":"## Revy code review\\n\\nTwo warnings on this revision.\\n\\n'
        "**Merge recommendation:** Review warnings before merge — no critical blockers flagged.\\n\\n"
        '**Confidence score:** 4/5\\n\\nScore is moderated by warning-level findings.\\n\\n'
        '### Findings\\n\\n| Severity | Category | Title | File |\\n'
        '| --- | --- | --- | --- |\\n| warning | bug | Issue | app/main.py |"}'
    )

    with patch("app.services.github_publish_formatter.settings") as mock_settings:
        mock_settings.reviewer_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 60
        mock_settings.revy_moonshot_model_for_profile.return_value = "model"
        mock_settings.app_public_url = "https://app.revy.dev"
        with patch(
            "app.services.github_publish_formatter.moonshot_review.complete_issue_comment_markdown",
            AsyncMock(return_value=moonshot_json),
        ):
            result = await build_pr_review_comment(ctx)

    assert result.startswith("## Revy code review")
    assert not result.startswith("{")
    assert "Confidence score" in result
    assert "Resolution metrics (this push)" in result


@pytest.mark.asyncio
async def test_build_pr_review_comment_falls_back_when_llm_returns_unparsed_json():
    from app.services.github_publish_formatter import build_pr_review_comment

    groups = [_group(severity=FindingSeverity.warning)]
    ctx = _ctx(groups)
    moonshot_json = '{"findings":[{"severity":"warning","title":"Issue"}]}'

    with patch("app.services.github_publish_formatter.settings") as mock_settings:
        mock_settings.reviewer_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 60
        mock_settings.revy_moonshot_model_for_profile.return_value = "model"
        mock_settings.app_public_url = "https://app.revy.dev"
        with patch(
            "app.services.github_publish_formatter.moonshot_review.complete_issue_comment_markdown",
            AsyncMock(return_value=moonshot_json),
        ):
            result = await build_pr_review_comment(ctx)
            expected = build_pr_review_comment_fallback(ctx)

    assert result == expected


def test_build_publish_format_result_splits_bodies():
    result = build_publish_format_result(_ctx([_group()]))
    assert result.check_summary != result.issue_comment
    assert "<details>" not in result.check_summary
    assert result.summary_json["confidence"] == result.confidence
    assert "active_count" in result.summary_json


def test_build_pr_review_comment_fallback_greptile_shape():
    groups = [
        _group(severity=FindingSeverity.warning, file_path="app/a.py", fingerprint="a"),
        _group(severity=FindingSeverity.error, file_path="app/b.py", fingerprint="b"),
        _group(
            resolution_method=ResolutionMethod.absent_and_addressed,
            state=GitHubFindingGroupState.resolved,
            fingerprint="c",
        ),
    ]
    markdown = build_pr_review_comment_fallback(_ctx(groups))
    assert "## Revy code review" in markdown
    narrative_pos = markdown.index("active finding")
    merge_pos = markdown.index("**Merge recommendation:**")
    confidence_pos = markdown.index("**Confidence score:**")
    assert narrative_pos < merge_pos < confidence_pos
    assert "Confidence score" in markdown
    assert "Score is" in markdown
    assert "### Files needing attention" in markdown
    assert "### Findings" in markdown
    assert "| Severity | Category | Title | File |" in markdown
    assert "<summary>Important files changed</summary>" in markdown
    assert "<summary>Review metadata</summary>" in markdown


def test_build_pr_review_comment_fallback_collapses_info_when_priority_exists():
    groups = [
        _group(severity=FindingSeverity.warning, title="Warn", fingerprint="w"),
        _group(severity=FindingSeverity.info, title="Info one", fingerprint="i1"),
        _group(severity=FindingSeverity.info, title="Info two", fingerprint="i2"),
    ]
    markdown = build_pr_review_comment_fallback(_ctx(groups))
    assert "### Findings" in markdown
    assert "<summary>2 informational findings</summary>" in markdown
    assert "Info one" in markdown
    assert "Warn" in markdown


def test_build_pr_review_comment_fallback_narrative_names_top_findings():
    groups = [
        _group(
            severity=FindingSeverity.error,
            title="Null deref",
            file_path="app/a.py",
            fingerprint="a",
        ),
    ]
    markdown = build_pr_review_comment_fallback(_ctx(groups))
    assert "**Null deref**" in markdown
    assert "`app/a.py`" in markdown


def test_build_pr_review_comment_fallback_security_details_row_cap():
    groups = [
        _group(
            severity=FindingSeverity.error,
            category=FindingCategory.security,
            title=f"Security issue {index}",
            fingerprint=f"s{index}",
        )
        for index in range(10)
    ]
    markdown = build_pr_review_comment_fallback(_ctx(groups))
    assert "2 more security finding(s)" in markdown


def test_build_pr_review_comment_fallback_includes_security_details():
    groups = [
        _group(
            severity=FindingSeverity.error,
            category=FindingCategory.security,
            title="Leaked secret",
            file_path="app/auth.py",
            fingerprint="sec",
        ),
    ]
    markdown = build_pr_review_comment_fallback(_ctx(groups))
    assert "<summary>Security review</summary>" in markdown
    assert "Leaked secret" in markdown
    assert "`app/auth.py`" in markdown


def test_build_pr_review_comment_fallback_includes_important_files_table():
    groups = [
        _group(file_path="app/a.py", title="Null deref", fingerprint="a"),
        _group(file_path="app/b.py", title="Race", fingerprint="b"),
    ]
    markdown = build_pr_review_comment_fallback(_ctx(groups))
    assert "<summary>Important files changed</summary>" in markdown
    assert "| File | Note |" in markdown
    assert "Null deref" in markdown


@pytest.mark.asyncio
async def test_build_pr_review_comment_moonshot_success_includes_greptile_sections():
    from app.services.github_publish_formatter import build_pr_review_comment

    groups = [_group(severity=FindingSeverity.warning)]
    ctx = _ctx(groups)
    moonshot_markdown = (
        "## Revy code review\n\n"
        "This revision introduces a warning in core logic that should be reviewed before merge.\n\n"
        "**Merge recommendation:** Review warnings before merge — no critical blockers flagged.\n\n"
        "**Confidence score:** 4/5\n\n"
        "Score is moderated by warning-level findings.\n\n"
        "### Findings\n\n"
        "| Severity | Category | Title | File |\n"
        "| --- | --- | --- | --- |\n"
        "| warning | bug | Issue | app/main.py |\n\n"
        "<details>\n<summary>Review metadata</summary>\n\n"
        "- head_sha: `abc123`\n\n</details>"
    )

    with patch("app.services.github_publish_formatter.settings") as mock_settings:
        mock_settings.reviewer_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 60
        mock_settings.revy_moonshot_model_for_profile.return_value = "model"
        mock_settings.app_public_url = "https://app.revy.dev"
        with patch(
            "app.services.github_publish_formatter.moonshot_review.complete_issue_comment_markdown",
            AsyncMock(return_value=moonshot_markdown),
        ):
            result = await build_pr_review_comment(ctx)

    assert result == moonshot_markdown
    assert "Confidence score" in result
    assert "moderated" in result
    assert "<details>" in result
    assert "Review metadata" in result


@pytest.mark.asyncio
async def test_build_pr_review_comment_thin_moonshot_returns_fallback():
    from app.services.github_publish_formatter import build_pr_review_comment

    groups = [_group(severity=FindingSeverity.warning)]
    ctx = _ctx(groups)
    thin_markdown = (
        "Automated review of PR #61 identified **1 active finding**.\n\n"
        "**Confidence:** 4/5\n\n"
        "| Severity | Category | Title | File |\n"
        "| --- | --- | --- | --- |\n"
        "| warning | bug | Issue | app/main.py |"
    )

    with patch("app.services.github_publish_formatter.settings") as mock_settings:
        mock_settings.reviewer_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 60
        mock_settings.revy_moonshot_model_for_profile.return_value = "model"
        mock_settings.app_public_url = "https://app.revy.dev"
        with patch(
            "app.services.github_publish_formatter.moonshot_review.complete_issue_comment_markdown",
            AsyncMock(return_value=thin_markdown),
        ):
            result = await build_pr_review_comment(ctx)
            expected = build_pr_review_comment_fallback(ctx)

    assert result == expected
    assert "## Revy code review" in result


@pytest.mark.asyncio
async def test_build_pr_review_comment_accepts_lowercase_score_rationale():
    from app.services.github_publish_formatter import build_pr_review_comment

    groups = [_group(severity=FindingSeverity.warning)]
    ctx = _ctx(groups)
    moonshot_markdown = (
        "## Revy code review\n\n"
        "This revision has one warning to review before merge.\n\n"
        "**Merge recommendation:** Review warnings before merge — no critical blockers flagged.\n\n"
        "**Confidence score:** 4/5\n\n"
        "The score is 4 because a warning remains on this revision.\n\n"
        "### Findings\n\n"
        "| Severity | Category | Title | File |\n"
        "| --- | --- | --- | --- |\n"
        "| warning | bug | Issue | app/main.py |\n"
    )

    with patch("app.services.github_publish_formatter.settings") as mock_settings:
        mock_settings.reviewer_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 60
        mock_settings.revy_moonshot_model_for_profile.return_value = "model"
        mock_settings.app_public_url = "https://app.revy.dev"
        with patch(
            "app.services.github_publish_formatter.moonshot_review.complete_issue_comment_markdown",
            AsyncMock(return_value=moonshot_markdown),
        ):
            result = await build_pr_review_comment(ctx)

    assert result.strip() == moonshot_markdown.strip()


@pytest.mark.asyncio
async def test_build_pr_review_comment_moonshot_failure_returns_fallback():
    from app.services.github_publish_formatter import build_pr_review_comment

    groups = [_group(severity=FindingSeverity.warning)]
    ctx = _ctx(groups)

    with patch("app.services.github_publish_formatter.settings") as mock_settings:
        mock_settings.reviewer_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 60
        mock_settings.revy_moonshot_model_for_profile.return_value = "model"
        mock_settings.app_public_url = "https://app.revy.dev"
        with patch(
            "app.services.github_publish_formatter.moonshot_review.complete_issue_comment_markdown",
            AsyncMock(side_effect=httpx.HTTPError("moonshot down")),
        ):
            result = await build_pr_review_comment(ctx)
            expected = build_pr_review_comment_fallback(ctx)

    assert result == expected
    assert result.strip()


def test_index_footer_on_fallback():
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=1,
        head_sha="sha",
        revision_number=1,
        groups=[],
        index_mode=GitHubIndexMode.full,
        fallback_reason="compare_failed",
    )
    markdown = build_pr_review_comment_fallback(ctx)
    assert "compare_failed" in markdown
    assert "Full-repo index" in markdown
