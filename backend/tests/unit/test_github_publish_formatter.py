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
            resolution_status=ResolutionStatus.addressed,
            state=GitHubFindingGroupState.superseded,
            fingerprint="a",
        ),
        _group(
            resolution_status=ResolutionStatus.judge_dismissed,
            state=GitHubFindingGroupState.resolved,
            fingerprint="b",
        ),
    ]
    prose = build_g9_resolution_prose(groups)
    assert "fixed since last push" in prose
    assert "dismissed by judge" in prose


def test_build_check_run_summary_is_compact():
    markdown = build_check_run_summary(_ctx([_group(severity=FindingSeverity.error)]))
    assert "**Confidence:**" in markdown
    assert "Since last push" not in markdown
    assert "| error |" in markdown or "FindingSeverity.error" in markdown


def test_build_pr_review_comment_fallback_includes_g9_and_metadata():
    groups = [
        _group(
            resolution_status=ResolutionStatus.addressed,
            state=GitHubFindingGroupState.superseded,
        ),
    ]
    markdown = build_pr_review_comment_fallback(_ctx(groups))
    assert "Confidence score" in markdown
    assert "Since last push" in markdown
    assert "<details>" in markdown
    assert "Open in Revy" in markdown


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
            resolution_status=ResolutionStatus.addressed,
            state=GitHubFindingGroupState.superseded,
            fingerprint="c",
        ),
    ]
    markdown = build_pr_review_comment_fallback(_ctx(groups))
    assert "## Revy code review" in markdown
    assert "Confidence score" in markdown
    assert "### Files needing attention" in markdown
    assert "### Findings" in markdown
    assert "| Severity | Category | Title | File |" in markdown


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
            "app.services.github_publish_formatter.moonshot_review.complete_review",
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
