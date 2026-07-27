# backend/tests/unit/test_github_publish_formatter.py
"""GitHub publish formatter — RQ7."""
import uuid

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
    assert result.summary_json["confidence"] == result.confidence
    assert "active_count" in result.summary_json


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
