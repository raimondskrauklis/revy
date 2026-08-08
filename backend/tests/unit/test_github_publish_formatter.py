# backend/tests/unit/test_github_publish_formatter.py
"""GitHub publish formatter — RQ7 + PSA two-block parity (staging dogfood post-#62)."""

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
    append_thread_resolve_skipped_block,
    apply_publish_summary_thread_collapse,
    build_check_run_summary,
    build_g9_resolution_prose,
    build_g9_resolution_prose_from_manifest,
    build_pr_review_comment_fallback,
    build_publish_format_result,
    compute_confidence,
    count_resolution_status,
    display_still_open_prior_count,
    extract_summary_blocks_section,
    filter_pr_active_groups_for_summary,
    format_resolution_metrics_block,
    format_summary_comment,
    format_thread_resolve_skipped_block,
    normalize_llm_issue_comment,
    splice_deterministic_findings_tables,
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


def test_publish_confidence_applies_generation_resolution_boost_to_pr_wide_verdict():
    resolved = _group(
        resolution_method=ResolutionMethod.absent_and_addressed,
        state=GitHubFindingGroupState.resolved,
        fingerprint="fixed",
    )
    prior_warning = _group(severity=FindingSeverity.warning, fingerprint="prior")
    severity_only = compute_confidence([prior_warning])
    with_boost = compute_confidence([prior_warning], resolution_groups=[resolved])
    assert with_boost >= severity_only
    from app.services.github_publish_formatter import _confidence_rationale

    rationale = _confidence_rationale([prior_warning], resolution_groups=[resolved])
    assert "Prior fixes or dismissals improved confidence" in rationale


def test_summary_json_active_count_fields_psa_d11():
    generation = [_group(severity=FindingSeverity.error, fingerprint="gen")]
    prior = _group(severity=FindingSeverity.warning, fingerprint="prior")
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=generation,
        pr_active_groups=[*generation, prior],
    )
    summary = build_publish_format_result(ctx).summary_json
    assert summary["generation_active_count"] == 1
    assert summary["pr_active_count"] == 2
    assert summary["active_count"] == summary["pr_active_count"]


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


def test_build_g9_resolution_prose_from_manifest():
    prose = build_g9_resolution_prose_from_manifest(
        {
            "transitions_addressed": 2,
            "transitions_dismissed": {"judge_dismissed": 1},
            "still_open_count": 3,
        }
    )
    assert "2 issues fixed since last push" in prose
    assert "dismissed by judge" in prose
    assert "3 still open from prior review" in prose


def test_summary_json_resolution_uses_manifest_when_present():
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=3,
        groups=[_group(resolution_status=ResolutionStatus.still_open)],
        resolution_metrics_manifest={
            "transitions_addressed": 1,
            "transitions_dismissed": {"verification_dismissed": 1},
            "still_open_count": 2,
        },
    )
    summary = build_publish_format_result(ctx).summary_json
    assert summary["resolution"]["addressed"] == 1
    assert summary["resolution"]["verification_dismissed"] == 1
    assert summary["resolution"]["still_open"] == 0


def test_build_pr_review_comment_fallback_g9_from_manifest_not_generation_groups():
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=3,
        groups=[
            _group(
                resolution_status=ResolutionStatus.addressed,
                state=GitHubFindingGroupState.active,
            )
        ],
        resolution_metrics_manifest={
            "transitions_addressed": 1,
            "transitions_dismissed": {},
            "still_open_count": 0,
            "resolution_rate_pct": 100.0,
            "transition_count": 1,
            "denominator_active_prior": 1,
            "compare_failed_count": 0,
        },
    )
    markdown = build_pr_review_comment_fallback(ctx)
    assert "**Since last push:** 1 issue fixed since last push" in markdown


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


def test_format_resolution_metrics_block_path_removed_line():
    block = format_resolution_metrics_block(
        {
            "resolution_rate_pct": 50.0,
            "transition_count": 1,
            "denominator_active_prior": 2,
            "transitions_addressed": 1,
            "transitions_dismissed": {},
            "still_open_count": 1,
            "compare_failed_count": 0,
            "hygiene_path_removed_count": 2,
        }
    )
    assert "Closed as path removed" in block
    assert "outside this push pair" in block


def test_format_thread_resolve_skipped_block():
    block = format_thread_resolve_skipped_block(
        {
            "thread_id_not_found": 3,
            "resolve_mutation_failed": 2,
            "already_resolved": 0,
            "thread_not_revy_owned": 0,
        }
    )
    assert block is not None
    assert "**Thread resolve skipped:** 5" in block
    assert "thread_id_not_found: 3" in block
    assert "resolve_mutation_failed: 2" in block


def test_append_thread_resolve_skipped_block_noop_when_zero():
    text = "## Revy review\n\nBody"
    assert (
        append_thread_resolve_skipped_block(
            text,
            {
                "thread_id_not_found": 0,
                "resolve_mutation_failed": 0,
                "already_resolved": 0,
                "thread_not_revy_owned": 0,
            },
        )
        == text
    )


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


def test_filter_pr_active_groups_for_summary_excludes_collapsed_inline():
    stale = _group(
        severity=FindingSeverity.warning,
        fingerprint="stale-fp",
        file_path="app/legacy.py",
    )
    current = _group(severity=FindingSeverity.info, fingerprint="new-fp")
    filtered = filter_pr_active_groups_for_summary(
        [stale, current],
        publishable_fingerprints={"new-fp"},
        collapsed_fingerprints={"stale-fp"},
    )
    assert [g.fingerprint for g in filtered] == ["new-fp"]


def test_filter_pr_active_groups_for_summary_keeps_addressed_pending_pass2_out():
    addressed = _group(
        severity=FindingSeverity.warning,
        fingerprint="fixed-fp",
        resolution_status=ResolutionStatus.addressed,
    )
    filtered = filter_pr_active_groups_for_summary(
        [addressed],
        publishable_fingerprints=set(),
        collapsed_fingerprints=set(),
    )
    assert filtered == []


def test_filter_pr_active_groups_for_summary_excludes_never_inlined_orphan():
    orphan = _group(
        severity=FindingSeverity.warning,
        fingerprint="orphan-fp",
        file_path="docs/plan.md",
        resolution_status=ResolutionStatus.still_open,
    )
    inlined = _group(
        severity=FindingSeverity.warning,
        fingerprint="inlined-fp",
        file_path="docs/other.md",
        resolution_status=ResolutionStatus.still_open,
    )
    filtered = filter_pr_active_groups_for_summary(
        [orphan, inlined],
        publishable_fingerprints=set(),
        collapsed_fingerprints=set(),
        generation_fingerprints=set(),
        ever_inlined_fingerprints={"inlined-fp"},
    )
    assert [g.fingerprint for g in filtered] == ["inlined-fp"]


def test_filter_pr_active_groups_for_summary_keeps_never_inlined_in_generation():
    orphan = _group(
        severity=FindingSeverity.warning,
        fingerprint="orphan-fp",
        file_path="docs/plan.md",
    )
    filtered = filter_pr_active_groups_for_summary(
        [orphan],
        publishable_fingerprints={"orphan-fp"},
        collapsed_fingerprints=set(),
        generation_fingerprints={"orphan-fp"},
        ever_inlined_fingerprints=set(),
    )
    assert [g.fingerprint for g in filtered] == ["orphan-fp"]


def test_filter_pr_active_groups_for_summary_keeps_orphan_when_generation_scope_unknown():
    orphan = _group(
        severity=FindingSeverity.warning,
        fingerprint="orphan-fp",
        file_path="docs/plan.md",
        resolution_status=ResolutionStatus.still_open,
    )
    filtered = filter_pr_active_groups_for_summary(
        [orphan],
        publishable_fingerprints=set(),
        collapsed_fingerprints=set(),
        generation_fingerprints=None,
        ever_inlined_fingerprints=set(),
    )
    assert [g.fingerprint for g in filtered] == ["orphan-fp"]


def test_format_resolution_metrics_block_display_still_open_override():
    block = format_resolution_metrics_block(
        {
            "resolution_rate_pct": 50.0,
            "transition_count": 1,
            "denominator_active_prior": 2,
            "transitions_addressed": 1,
            "transitions_dismissed": {},
            "still_open_count": 1,
            "compare_failed_count": 0,
        },
        display_still_open_prior=0,
    )
    assert "Still open from prior review" not in block
    assert "100.0% (1/1 prior active)" in block


def test_format_resolution_metrics_block_display_override_includes_compare_failed():
    block = format_resolution_metrics_block(
        {
            "resolution_rate_pct": 50.0,
            "transition_count": 1,
            "denominator_active_prior": 2,
            "transitions_addressed": 1,
            "transitions_dismissed": {},
            "still_open_count": 1,
            "compare_failed_count": 1,
        },
        display_still_open_prior=0,
    )
    assert "100.0% (1/1 prior active)" in block
    assert "Compare blocked" in block


def test_format_resolution_metrics_block_display_override_caps_hidden_still_open():
    block = format_resolution_metrics_block(
        {
            "resolution_rate_pct": 50.0,
            "transition_count": 1,
            "denominator_active_prior": 2,
            "transitions_addressed": 1,
            "transitions_dismissed": {},
            "still_open_count": 0,
            "compare_failed_count": 0,
        },
        display_still_open_prior=1,
    )
    assert "50.0% (1/2 prior active)" in block


def test_build_g9_resolution_prose_from_manifest_display_still_open_override():
    prose = build_g9_resolution_prose_from_manifest(
        {
            "transitions_addressed": 1,
            "still_open_count": 1,
            "transitions_dismissed": {},
        },
        display_still_open_prior=0,
    )
    assert "1 issue fixed since last push" in prose
    assert "still open" not in prose


def test_clean_generation_hides_orphan_from_block2_and_narrative():
    orphan = _group(
        severity=FindingSeverity.warning,
        fingerprint="orphan-fp",
        file_path="docs/plan.md",
        title="Corpus sync prose",
        resolution_status=ResolutionStatus.still_open,
    )
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=491,
        head_sha="abc123",
        revision_number=3,
        groups=[],
        pr_active_groups=[orphan],
        ever_inlined_fingerprints=frozenset(),
        resolution_metrics_manifest={
            "resolution_rate_pct": 50.0,
            "transition_count": 1,
            "denominator_active_prior": 2,
            "transitions_addressed": 1,
            "transitions_dismissed": {},
            "still_open_count": 1,
            "compare_failed_count": 0,
        },
    )
    filtered_ctx = PublishFormatContext(
        pull_request_id=ctx.pull_request_id,
        pull_request_number=ctx.pull_request_number,
        head_sha=ctx.head_sha,
        revision_number=ctx.revision_number,
        groups=ctx.groups,
        resolution_metrics_manifest=ctx.resolution_metrics_manifest,
        pr_active_groups=filter_pr_active_groups_for_summary(
            [orphan],
            publishable_fingerprints=set(),
            collapsed_fingerprints=set(),
            generation_fingerprints=set(),
            ever_inlined_fingerprints=set(),
        ),
        ever_inlined_fingerprints=frozenset(),
    )
    assert display_still_open_prior_count(filtered_ctx) == 0
    summary = build_publish_format_result(filtered_ctx).summary_json
    assert summary["resolution"]["still_open"] == 0
    assert summary["pr_active_count"] == 0
    issue = build_pr_review_comment_fallback(filtered_ctx)
    assert "Corpus sync prose" not in issue
    assert "docs/plan.md" not in issue
    assert "Still open from prior review" not in issue
    assert "without active findings" in issue.lower()


def test_apply_publish_summary_thread_collapse_literal_merge_replacement():
    stale = _group(
        severity=FindingSeverity.warning,
        fingerprint="stale-fp",
        file_path="app/legacy.py",
    )
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=[],
        pr_active_groups=[stale],
    )
    issue = (
        "## Revy code review\n\n"
        "Narrative.\n\n"
        "**Merge recommendation:** hold (1 finding)\n\n"
        "**Confidence score:** 3/5\n\n"
        "Rationale.\n\n"
        "### This generation\n\n"
        "No publishable findings this generation.\n\n"
        "### Still open on PR\n\n"
        "| Severity | Category | Title | File |\n"
        "| --- | --- | --- | --- |\n"
        "| warning | bug | Stale | app/legacy.py |\n"
    )
    check = build_check_run_summary(ctx)
    result = apply_publish_summary_thread_collapse(
        check,
        issue,
        ctx,
        publishable_fingerprints=set(),
        collapsed_fingerprints={"stale-fp"},
    )
    assert "app/legacy.py" not in result.issue_comment
    assert "**Merge recommendation:**" in result.issue_comment


def test_refresh_issue_pr_verdict_sections_removes_empty_security_block():
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=[],
        pr_active_groups=[],
    )
    issue = (
        "## Revy code review\n\n"
        "**Merge recommendation:** hold\n\n"
        "**Confidence score:** 3/5\n\n"
        "<details>\n"
        "<summary>Security review</summary>\n\n"
        "- Old security finding (`app/auth.py`)\n\n"
        "</details>\n\n"
        "### This generation\n\n"
        "No publishable findings this generation.\n\n"
        "### Still open on PR\n\n"
        "No open findings on this pull request.\n"
    )
    from app.services.github_publish_formatter import _refresh_issue_pr_verdict_sections

    refreshed = _refresh_issue_pr_verdict_sections(issue, ctx)
    assert "Security review" not in refreshed
    assert "app/auth.py" not in refreshed


def test_patch_issue_narrative_paragraph_updates_open_finding_count():
    stale = _group(
        severity=FindingSeverity.warning,
        fingerprint="stale-fp",
        file_path="app/legacy.py",
    )
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=[],
        pr_active_groups=[stale],
    )
    issue = (
        "## Revy code review\n\n"
        "This revision added no new publishable findings, but **2** findings remain open on PR #42.\n\n"
        "**Merge recommendation:** hold\n\n"
        "### This generation\n\n"
        "No publishable findings this generation.\n"
    )
    from app.services.github_publish_formatter import _patch_issue_narrative_paragraph

    refreshed = _patch_issue_narrative_paragraph(issue, ctx)
    assert "**1** finding remain open on PR #42" in refreshed
    assert "**2**" not in refreshed


def test_splice_deterministic_findings_tables_replaces_llm_mismatch():
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
        revision_number=1,
        groups=generation,
        pr_active_groups=[*generation, prior_only],
    )
    llm_markdown = (
        "## Revy code review\n\n"
        "Narrative.\n\n"
        "### This generation findings\n\n"
        "| Severity | Category | Title | File |\n"
        "| --- | --- | --- | --- |\n"
        "| error | bug | Issue | app/main.py |\n\n"
        "### Still open on PR findings\n\n"
        "| Severity | Category | Title | File |\n"
        "| --- | --- | --- | --- |\n"
        "| error | bug | Issue | app/main.py |\n"
        "| warning | bug | Issue | app/legacy.py |\n\n"
        "<details><summary>Review metadata</summary></details>"
    )
    result = splice_deterministic_findings_tables(llm_markdown, ctx)
    assert "app/legacy.py" in result
    assert "### This generation findings" not in result
    assert extract_summary_blocks_section(result) == format_summary_comment(
        generation_groups=generation,
        pr_active_groups=[*generation, prior_only],
    )


def test_build_pr_review_comment_fallback_two_block_when_pr_active_extra():
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
    assert "app/legacy.py" in markdown
    assert "### Still open on PR" in markdown
    assert "### This generation" in markdown


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
    wrapped = '{"body":"## Revy code review\\n\\n**Confidence score:** 4/5\\n\\n### Findings"}'
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
        "**Confidence score:** 4/5\\n\\nScore is moderated by warning-level findings.\\n\\n"
        "### This generation\\n\\n| Severity | Category | Title | File |\\n"
        "| --- | --- | --- | --- |\\n| warning | bug | Issue | app/main.py |\\n\\n"
        "### Still open on PR\\n\\n| Severity | Category | Title | File |\\n"
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
    assert "generation_active_count" in result.summary_json
    assert "pr_active_count" in result.summary_json


def test_merge_recommendation_uses_pr_active_when_generation_clean():
    prior_only = _group(
        severity=FindingSeverity.error,
        fingerprint="prior",
        file_path="app/legacy.py",
    )
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=[],
        pr_active_groups=[prior_only],
    )
    markdown = build_pr_review_comment_fallback(ctx)
    assert "Ready to merge" not in markdown
    assert "Fix before merge" in markdown
    assert compute_confidence([prior_only]) <= 3
    assert "no active findings" not in markdown.lower()


def test_confidence_rationale_pr_wide_when_generation_clean():
    prior_only = _group(
        severity=FindingSeverity.error,
        fingerprint="prior",
        file_path="app/legacy.py",
    )
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=[],
        pr_active_groups=[prior_only],
    )
    markdown = build_pr_review_comment_fallback(ctx)
    assert "no active findings on this revision" not in markdown.lower()
    assert "critical or error" in markdown.lower()


def test_check_and_issue_share_identical_summary_blocks():
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
    from app.services.github_publish_formatter import extract_summary_blocks_section

    check_blocks = extract_summary_blocks_section(build_check_run_summary(ctx))
    issue_blocks = extract_summary_blocks_section(build_pr_review_comment_fallback(ctx))
    assert check_blocks is not None
    assert issue_blocks == check_blocks


def test_narrative_warns_on_pr_wide_error_when_generation_info_only():
    generation = [_group(severity=FindingSeverity.info, fingerprint="new-info")]
    prior_error = _group(
        severity=FindingSeverity.error,
        fingerprint="prior-err",
        file_path="app/legacy.py",
    )
    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=3,
        groups=generation,
        pr_active_groups=[*generation, prior_error],
    )
    markdown = build_pr_review_comment_fallback(ctx)
    assert "Fix before merge" in markdown
    assert "Address critical or error findings before merge." in markdown
    assert "merge risk appears low" not in markdown.lower()


def test_build_issue_comment_user_prompt_includes_two_block_instruction():
    from app.services.github_publish_formatter import _build_issue_comment_user_prompt

    groups = [_group(severity=FindingSeverity.warning)]
    ctx = _ctx(groups)
    prompt = _build_issue_comment_user_prompt(ctx)
    assert "### This generation" in prompt
    assert "### Still open on PR" in prompt
    assert "PR-wide still-open findings JSON" in prompt


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
    assert "### This generation" in markdown
    assert "### Still open on PR" in markdown
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
    assert "### This generation" in markdown
    assert "Info one" in markdown
    assert "Warn" in markdown
    assert "<summary>2 informational findings</summary>" not in markdown


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


def test_build_pr_review_comment_fallback_narrative_escapes_title_markdown():
    groups = [
        _group(
            severity=FindingSeverity.warning,
            title="Use `foo_*` safely",
            file_path="app/a.py",
            fingerprint="a",
        ),
    ]
    markdown = build_pr_review_comment_fallback(_ctx(groups))
    assert "**Use \\`foo\\_\\*\\` safely**" in markdown


def test_insert_resolution_metrics_block_before_summary_blocks():
    from app.services.github_publish_formatter import _insert_resolution_metrics_block

    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=2,
        groups=[_group()],
        resolution_metrics_manifest={
            "resolution_rate_pct": 50.0,
            "transition_count": 1,
            "denominator_active_prior": 2,
            "transitions_addressed": 1,
            "transitions_dismissed": {},
            "compare_failed_count": 0,
            "still_open_count": 1,
        },
    )
    moonshot = (
        "## Revy code review\n\n"
        "Narrative.\n\n"
        "**Merge recommendation:** Review.\n\n"
        "**Confidence score:** 4/5\n\n"
        "The score is 4 because warnings remain.\n\n"
        "### This generation\n\n"
        "| Severity | Category | Title | File |\n"
    )
    result = _insert_resolution_metrics_block(moonshot, ctx)
    metrics_idx = result.find("### Resolution metrics")
    generation_idx = result.find("### This generation")
    assert metrics_idx >= 0
    assert generation_idx > metrics_idx


def test_has_confidence_rationale_ignores_score_is_in_finding_title():
    from app.services.github_publish_formatter import _has_confidence_rationale_in_comment

    markdown = (
        "## Revy code review\n\n"
        "**Merge recommendation:** Review.\n\n"
        "**Confidence score:** 4/5\n\n"
        "Moderated by remaining findings.\n\n"
        "### Findings\n\n"
        "| warning | bug | The score is wrong | app/main.py |\n"
    )
    assert _has_confidence_rationale_in_comment(markdown) is False


def test_build_pr_review_comment_fallback_security_details_escapes_inline_markdown():
    groups = [
        _group(
            severity=FindingSeverity.error,
            category=FindingCategory.security,
            title="Use `foo_*` token",
            fingerprint="s1",
        ),
    ]
    markdown = build_pr_review_comment_fallback(_ctx(groups))
    assert "Use \\`foo\\_\\*\\` token" in markdown


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
        "### This generation\n\n"
        "| Severity | Category | Title | File |\n"
        "| --- | --- | --- | --- |\n"
        "| warning | bug | Issue | app/main.py |\n\n"
        "### Still open on PR\n\n"
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

    assert "This revision introduces a warning" in result
    assert format_summary_comment(generation_groups=groups, pr_active_groups=groups) in result
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
        "### This generation\n\n"
        "| Severity | Category | Title | File |\n"
        "| --- | --- | --- | --- |\n"
        "| warning | bug | Issue | app/main.py |\n\n"
        "### Still open on PR\n\n"
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

    assert "The score is 4 because" in result
    assert format_summary_comment(generation_groups=groups, pr_active_groups=groups) in result


@pytest.mark.asyncio
async def test_build_pr_review_comment_accepts_confidence_is_because_rationale():
    from app.services.github_publish_formatter import build_pr_review_comment

    groups = [_group(severity=FindingSeverity.warning)]
    ctx = _ctx(groups)
    moonshot_markdown = (
        "## Revy code review\n\n"
        "This revision has one warning to review before merge.\n\n"
        "**Merge recommendation:** Review warnings before merge — no critical blockers flagged.\n\n"
        "**Confidence score:** 4/5\n\n"
        "Confidence is 4 because a warning remains on this revision.\n\n"
        "### This generation\n\n"
        "| Severity | Category | Title | File |\n"
        "| --- | --- | --- | --- |\n"
        "| warning | bug | Issue | app/main.py |\n\n"
        "### Still open on PR\n\n"
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

    assert "Confidence is 4 because" in result
    assert format_summary_comment(generation_groups=groups, pr_active_groups=groups) in result


@pytest.mark.asyncio
async def test_build_pr_review_comment_moonshot_missing_pr_block_returns_fallback():
    from app.services.github_publish_formatter import build_pr_review_comment

    groups = [_group(severity=FindingSeverity.warning)]
    ctx = _ctx(groups)
    legacy_markdown = (
        "## Revy code review\n\n"
        "Narrative.\n\n"
        "**Merge recommendation:** Review warnings before merge — no critical blockers flagged.\n\n"
        "**Confidence score:** 4/5\n\n"
        "Score is moderated by warning-level findings.\n\n"
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
            AsyncMock(return_value=legacy_markdown),
        ):
            result = await build_pr_review_comment(ctx)
            expected = build_pr_review_comment_fallback(ctx)

    assert result == expected


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
