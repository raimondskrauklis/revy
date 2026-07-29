# backend/app/services/github_publish_formatter.py
"""Greptile-shaped GitHub publish formatting — RQ7 + PSA two-block parity.

Surface contract (PSA-D1–D4, PSA-D12):
- Check + issue comment share ``format_summary_comment`` (this generation + still open on PR).
- Verdict fields (confidence, merge, rationale, files, security rollups) use PR-wide active groups.
- Verdict confidence applies generation resolution boost from ``ctx.groups`` (PSA-D3).
- G9 / resolution metrics stay generation-scoped.
- Inline publish remains generation-only; ``compute_check_conclusion`` unchanged (generation-scoped).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from uuid import UUID

import httpx

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubIndexMode,
    ResolutionMethod,
    ResolutionStatus,
    stored_enum_value,
)
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.core.logging import get_logger
from app.integrations import moonshot_review
from app.models.github_finding_group import GitHubFindingGroupORM

logger = get_logger(__name__)

FILES_NEEDING_ATTENTION_CAP = 20
IMPORTANT_FILES_ROW_CAP = 8
SECURITY_DETAILS_ROW_CAP = 8
SUMMARY_ROW_CAP = 50

_SEVERITY_RANK = {
    FindingSeverity.critical.value: 0,
    FindingSeverity.error.value: 1,
    FindingSeverity.warning.value: 2,
    FindingSeverity.info.value: 3,
}

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL | re.IGNORECASE)

_LLM_ISSUE_COMMENT_JSON_KEYS = (
    "body",
    "comment",
    "markdown",
    "content",
    "review_comment",
    "issue_comment",
)


def _looks_like_json_wrapper(text: str) -> bool:
    stripped = text.strip()
    if not stripped.startswith("{") or not stripped.endswith("}"):
        return False
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return False
    return isinstance(payload, dict) and any(k in payload for k in _LLM_ISSUE_COMMENT_JSON_KEYS)


def normalize_llm_issue_comment(raw: str) -> str | None:
    """Strip JSON wrappers Moonshot sometimes returns instead of raw markdown."""
    text = raw.strip()
    if not text:
        return None

    fence_match = _JSON_FENCE_RE.match(text)
    if fence_match:
        text = fence_match.group(1).strip()

    if text.startswith("{") and text.endswith("}"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return raw.strip()
        if isinstance(payload, dict):
            for key in _LLM_ISSUE_COMMENT_JSON_KEYS:
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            return None

    return raw.strip()


def _revy_ui_link(pull_request_id: UUID) -> str:
    base = (settings.app_public_url or "https://app.revy.dev").rstrip("/")
    return f"{base}/reviewer/pull-requests/{pull_request_id}"


def _escape_markdown_table_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _escape_markdown_inline(value: str) -> str:
    """Escape metacharacters when wrapping user text in bold or list markdown."""
    return (
        _escape_markdown_table_cell(value)
        .replace("`", "\\`")
        .replace("*", "\\*")
        .replace("_", "\\_")
    )


@dataclass(frozen=True)
class PublishFormatContext:
    pull_request_id: UUID
    pull_request_number: int
    head_sha: str
    revision_number: int
    groups: list[GitHubFindingGroupORM]
    index_mode: GitHubIndexMode | str | None = None
    fallback_reason: str | None = None
    resolution_metrics_manifest: dict[str, object] | None = None
    pr_active_groups: list[GitHubFindingGroupORM] | None = None


@dataclass(frozen=True)
class PublishFormatResult:
    check_summary: str
    issue_comment: str
    confidence: int
    summary_json: dict


def verdict_groups(ctx: PublishFormatContext) -> list[GitHubFindingGroupORM]:
    """PR-wide active groups for verdict copy; falls back to generation groups."""
    if ctx.pr_active_groups is not None:
        return ctx.pr_active_groups
    return ctx.groups


def extract_summary_blocks_section(markdown: str) -> str | None:
    """Substring from ### This generation through ### Still open on PR block (parity tests)."""
    start = markdown.find("### This generation")
    if start < 0:
        return None
    still_open = markdown.find("### Still open on PR", start)
    if still_open < 0:
        return None
    tail = markdown[still_open:]
    end_offset = len(tail)
    for marker in ("\n### ", "\n<details>", "\n---"):
        idx = tail.find(marker, len("### Still open on PR"))
        if idx > 0:
            end_offset = min(end_offset, idx)
    return markdown[start : still_open + end_offset].strip()


def count_resolution_status(groups: list[GitHubFindingGroupORM]) -> dict[str, int]:
    counts = {
        ResolutionStatus.addressed.value: 0,
        ResolutionStatus.judge_dismissed.value: 0,
        ResolutionMethod.verification_dismissed.value: 0,
        ResolutionMethod.human_dismissed.value: 0,
        ResolutionStatus.still_open.value: 0,
    }
    for group in groups:
        if group.state == GitHubFindingGroupState.resolved and group.resolution_method is not None:
            if group.resolution_method == ResolutionMethod.absent_and_addressed:
                counts[ResolutionStatus.addressed.value] += 1
            elif group.resolution_method == ResolutionMethod.judge_dismissed:
                counts[ResolutionStatus.judge_dismissed.value] += 1
            elif group.resolution_method == ResolutionMethod.verification_dismissed:
                counts[ResolutionMethod.verification_dismissed.value] += 1
            elif group.resolution_method == ResolutionMethod.human_dismissed:
                counts[ResolutionMethod.human_dismissed.value] += 1
            continue
        if group.resolution_status is None:
            continue
        if (
            group.resolution_status == ResolutionStatus.still_open
            and group.state == GitHubFindingGroupState.active
        ):
            counts[ResolutionStatus.still_open.value] += 1
    return counts


def format_resolution_metrics_block(manifest: dict[str, object]) -> str:
    """FR-Q12 transitions block from reconcile manifest resolution_pass."""
    rate = manifest.get("resolution_rate_pct", 0.0)
    addressed = manifest.get("transitions_addressed", 0)
    dismissed = manifest.get("transitions_dismissed", {})
    still_open = manifest.get("still_open_count")
    denominator = manifest.get("denominator_active_prior", 0)
    compare_failed = manifest.get("compare_failed_count", 0)

    dismissed_parts: list[str] = []
    if isinstance(dismissed, dict):
        for method, label in (
            (ResolutionMethod.judge_dismissed.value, "judge"),
            (ResolutionMethod.verification_dismissed.value, "verification"),
            (ResolutionMethod.human_dismissed.value, "human"),
        ):
            count = dismissed.get(method, 0)
            if isinstance(count, int) and count > 0:
                dismissed_parts.append(f"{count} by {label}")

    lines = [
        "### Resolution metrics (this push)",
        "",
        f"- **Resolution rate:** {rate}% ({manifest.get('transition_count', 0)}/{denominator} prior active)",
        f"- **Closed as fixed:** {addressed}",
    ]
    if dismissed_parts:
        lines.append(f"- **Dismissed:** {', '.join(dismissed_parts)}")
    if isinstance(still_open, int) and still_open > 0:
        lines.append(f"- **Still open from prior review:** {still_open}")
    if isinstance(compare_failed, int) and compare_failed > 0:
        lines.append(f"- **Compare blocked:** {compare_failed} group(s)")
    return "\n".join(lines)


def _severity_rank(severity: FindingSeverity | str) -> int:
    return _SEVERITY_RANK.get(stored_enum_value(severity), 99)


def _sorted_active_groups(groups: list[GitHubFindingGroupORM]) -> list[GitHubFindingGroupORM]:
    return sorted(
        _active_groups(groups),
        key=lambda group: (
            _severity_rank(group.severity),
            stored_enum_value(group.category),
            group.title,
        ),
    )


def _confidence_ceiling(groups: list[GitHubFindingGroupORM]) -> int:
    active = _active_groups(groups)
    if not active:
        return 5
    if any(g.severity in (FindingSeverity.critical, FindingSeverity.error) for g in active):
        return 3
    if any(g.severity == FindingSeverity.warning for g in active):
        return 4
    return 5


def compute_confidence(
    groups: list[GitHubFindingGroupORM],
    *,
    resolution_groups: list[GitHubFindingGroupORM] | None = None,
) -> int:
    active = _active_groups(groups)
    if not active:
        return 5

    score = 5
    if any(g.severity in (FindingSeverity.critical, FindingSeverity.error) for g in active):
        score -= 2
    elif any(g.severity == FindingSeverity.warning for g in active):
        score -= 1

    resolution_source = resolution_groups if resolution_groups is not None else groups
    resolution = count_resolution_status(resolution_source)
    score += min(2, resolution[ResolutionStatus.addressed.value])
    dismissed_total = (
        resolution[ResolutionStatus.judge_dismissed.value]
        + resolution[ResolutionMethod.verification_dismissed.value]
        + resolution[ResolutionMethod.human_dismissed.value]
    )
    score += min(1, dismissed_total)
    return max(0, min(_confidence_ceiling(groups), score))


def compute_publish_confidence(ctx: PublishFormatContext) -> int:
    """PR-wide severity with generation-scoped resolution boost (PSA-D3)."""
    verdict = verdict_groups(ctx)
    return compute_confidence(verdict, resolution_groups=ctx.groups)


def build_g9_resolution_prose(groups: list[GitHubFindingGroupORM]) -> str:
    counts = count_resolution_status(groups)
    parts: list[str] = []
    if counts[ResolutionStatus.addressed.value]:
        n = counts[ResolutionStatus.addressed.value]
        parts.append(f"{n} issue{'s' if n != 1 else ''} fixed since last push")
    for method, label in (
        (ResolutionStatus.judge_dismissed.value, "judge"),
        (ResolutionMethod.verification_dismissed.value, "verification"),
        (ResolutionMethod.human_dismissed.value, "human"),
    ):
        if counts[method]:
            n = counts[method]
            parts.append(f"{n} dismissed by {label}")
    if counts[ResolutionStatus.still_open.value]:
        n = counts[ResolutionStatus.still_open.value]
        parts.append(f"{n} still open from prior review")
    return "; ".join(parts)


def build_g9_resolution_prose_from_manifest(manifest: dict[str, object]) -> str:
    """G9 prose from reconcile resolution_pass manifest (FR-DG1)."""
    parts: list[str] = []
    addressed = int(manifest.get("transitions_addressed") or 0)
    if addressed:
        parts.append(f"{addressed} issue{'s' if addressed != 1 else ''} fixed since last push")
    dismissed = manifest.get("transitions_dismissed")
    if isinstance(dismissed, dict):
        for key, label in (
            ("judge_dismissed", "judge"),
            ("verification_dismissed", "verification"),
            ("human_dismissed", "human"),
        ):
            count = int(dismissed.get(key) or 0)
            if count:
                parts.append(f"{count} dismissed by {label}")
    still_open = int(manifest.get("still_open_count") or 0)
    if still_open:
        parts.append(f"{still_open} still open from prior review")
    return "; ".join(parts)


def resolution_counts_from_manifest(manifest: dict[str, object]) -> dict[str, int]:
    dismissed = manifest.get("transitions_dismissed")
    if not isinstance(dismissed, dict):
        dismissed = {}
    return {
        ResolutionStatus.addressed.value: int(manifest.get("transitions_addressed") or 0),
        ResolutionStatus.judge_dismissed.value: int(dismissed.get("judge_dismissed") or 0),
        ResolutionMethod.verification_dismissed.value: int(
            dismissed.get("verification_dismissed") or 0
        ),
        ResolutionMethod.human_dismissed.value: int(dismissed.get("human_dismissed") or 0),
        ResolutionStatus.still_open.value: int(manifest.get("still_open_count") or 0),
    }


def _g9_resolution_prose_for_ctx(ctx: PublishFormatContext) -> str:
    if ctx.resolution_metrics_manifest is not None:
        return build_g9_resolution_prose_from_manifest(ctx.resolution_metrics_manifest)
    return build_g9_resolution_prose(ctx.groups)


def _active_groups(groups: list[GitHubFindingGroupORM]) -> list[GitHubFindingGroupORM]:
    return [g for g in groups if g.state == GitHubFindingGroupState.active]


def _severity_table_rows(
    groups: list[GitHubFindingGroupORM],
    *,
    row_cap: int = SUMMARY_ROW_CAP,
) -> list[str]:
    active = _sorted_active_groups(groups)[:row_cap]
    rows = [
        "| Severity | Category | Title | File |",
        "| --- | --- | --- | --- |",
    ]
    for group in active:
        file_cell = _escape_markdown_table_cell(group.file_path or "—")
        title_cell = _escape_markdown_table_cell(group.title)
        rows.append(
            f"| {stored_enum_value(group.severity)} | {stored_enum_value(group.category)} "
            f"| {title_cell} | {file_cell} |"
        )
    return rows


def format_summary_comment(
    *,
    generation_groups: list[GitHubFindingGroupORM],
    pr_active_groups: list[GitHubFindingGroupORM],
) -> str:
    """FR-Q7 two-block summary: this generation + PR-level still open."""
    generation_active = _active_groups(generation_groups)
    pr_active = _active_groups(pr_active_groups)

    lines = [
        "### This generation",
        "",
    ]
    if generation_active:
        lines.extend(_severity_table_rows(generation_groups))
        if len(generation_active) > SUMMARY_ROW_CAP:
            lines.extend(["", f"_Showing {SUMMARY_ROW_CAP} of {len(generation_active)} findings._"])
    else:
        lines.append("No publishable findings this generation.")

    lines.extend(["", "### Still open on PR", ""])
    if pr_active:
        lines.extend(_severity_table_rows(pr_active_groups))
        if len(pr_active) > SUMMARY_ROW_CAP:
            lines.extend(["", f"_Showing {SUMMARY_ROW_CAP} of {len(pr_active)} findings._"])
    else:
        lines.append("No open findings on this pull request.")

    return "\n".join(lines)


def build_check_run_summary(ctx: PublishFormatContext) -> str:
    """G3 compact body for GitHub check run output."""
    verdict = verdict_groups(ctx)
    confidence = compute_publish_confidence(ctx)
    lines = [
        "## Revy review",
        "",
        f"**Confidence:** {confidence}/5",
        "",
        format_summary_comment(
            generation_groups=ctx.groups,
            pr_active_groups=verdict,
        ),
    ]
    return "\n".join(lines)


def _files_needing_attention(groups: list[GitHubFindingGroupORM]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for group in _sorted_active_groups(groups):
        if group.severity == FindingSeverity.info:
            continue
        if not group.file_path or group.file_path in seen:
            continue
        seen.add(group.file_path)
        paths.append(group.file_path)
        if len(paths) >= FILES_NEEDING_ATTENTION_CAP:
            break
    return paths


def _merge_recommendation(groups: list[GitHubFindingGroupORM]) -> str:
    active = _active_groups(groups)
    if not active:
        return "Ready to merge — no active findings on this pull request."
    if any(g.severity in (FindingSeverity.critical, FindingSeverity.error) for g in active):
        return "Fix before merge — critical or error-severity findings need attention."
    if any(g.severity == FindingSeverity.warning for g in active):
        return "Review warnings before merge — no critical blockers flagged."
    return "Informational findings only — merge risk appears low pending your judgment."


def _top_finding_summaries(groups: list[GitHubFindingGroupORM], *, limit: int = 3) -> list[str]:
    summaries: list[str] = []
    for group in _sorted_active_groups(groups):
        if group.severity == FindingSeverity.info:
            continue
        location = f" in `{group.file_path}`" if group.file_path else ""
        summaries.append(f"**{_escape_markdown_inline(group.title)}**{location}")
        if len(summaries) >= limit:
            break
    return summaries


def _index_footer(ctx: PublishFormatContext) -> str:
    lines: list[str] = []
    if ctx.fallback_reason:
        lines.append(f"_Index fallback: {ctx.fallback_reason}_")
    index_mode = stored_enum_value(ctx.index_mode) if ctx.index_mode is not None else None
    if index_mode == GitHubIndexMode.full.value:
        lines.append("_Full-repo index (deep/critical profile)._")
    return "\n".join(lines)


def _resolution_metrics_block(ctx: PublishFormatContext) -> str | None:
    if ctx.resolution_metrics_manifest is None:
        return None
    return format_resolution_metrics_block(ctx.resolution_metrics_manifest)


def _has_resolution_progress(groups: list[GitHubFindingGroupORM]) -> bool:
    counts = count_resolution_status(groups)
    return any(
        counts[key] > 0
        for key in (
            ResolutionStatus.addressed.value,
            ResolutionStatus.judge_dismissed.value,
            ResolutionMethod.verification_dismissed.value,
            ResolutionMethod.human_dismissed.value,
        )
    )


def _confidence_rationale(
    groups: list[GitHubFindingGroupORM],
    *,
    resolution_groups: list[GitHubFindingGroupORM] | None = None,
) -> str:
    active = _active_groups(groups)
    confidence = compute_confidence(groups, resolution_groups=resolution_groups)
    resolution_source = resolution_groups if resolution_groups is not None else groups
    if not active:
        return "Score is 5 because there are no active findings on this pull request."
    if confidence <= 2:
        return "Score is low due to critical or error-severity findings that need attention before merge."
    if confidence == 3:
        return "Score is moderated by active findings that still need review before merge."
    if confidence == 4:
        base = "Score is good but not perfect: some active findings remain."
        if _has_resolution_progress(resolution_source):
            return f"{base} Prior fixes or dismissals improved confidence."
        return base
    if any(g.severity != FindingSeverity.info for g in active):
        return "Score is high relative to remaining active findings on this revision."
    return "Score is high with only informational findings on this revision."


def publish_confidence_rationale(ctx: PublishFormatContext) -> str:
    verdict = verdict_groups(ctx)
    return _confidence_rationale(verdict, resolution_groups=ctx.groups)


def _review_narrative_paragraph(ctx: PublishFormatContext) -> str:
    generation_active = _active_groups(ctx.groups)
    verdict = verdict_groups(ctx)
    pr_active = _active_groups(verdict)

    if not generation_active and not pr_active:
        return (
            "This revision completed without active findings that need follow-up. "
            "No merge blockers were identified from the automated review on this push."
        )

    if not generation_active and pr_active:
        top_summaries = _top_finding_summaries(verdict)
        lead = (
            f"This revision added no new publishable findings, but **{len(pr_active)}** "
            f"finding{'s' if len(pr_active) != 1 else ''} remain open on PR "
            f"#{ctx.pull_request_number}."
        )
        if top_summaries:
            lead = f"{lead} Top items: {', '.join(top_summaries)}."
    else:
        top_summaries = _top_finding_summaries(ctx.groups)
        if top_summaries:
            lead = (
                f"This revision has **{len(generation_active)}** active finding"
                f"{'s' if len(generation_active) != 1 else ''} on PR #{ctx.pull_request_number}. "
                f"Top items: {', '.join(top_summaries)}."
            )
        else:
            lead = (
                f"This revision has **{len(generation_active)}** informational finding"
                f"{'s' if len(generation_active) != 1 else ''} on PR #{ctx.pull_request_number}."
            )
        if len(pr_active) > len(generation_active):
            lead = (
                f"{lead} **{len(pr_active)}** finding"
                f"{'s' if len(pr_active) != 1 else ''} remain open on this pull request overall."
            )

    if any(g.severity in (FindingSeverity.critical, FindingSeverity.error) for g in pr_active):
        return f"{lead} Address critical or error findings before merge."
    if any(g.severity == FindingSeverity.warning for g in pr_active):
        return f"{lead} Review warnings before merge; no critical blockers were flagged."
    return f"{lead} Findings are informational; merge risk appears low pending your judgment."


def _security_details_lines(groups: list[GitHubFindingGroupORM]) -> list[str] | None:
    security_findings = _sorted_active_groups(
        [group for group in groups if group.category == FindingCategory.security]
    )
    if not security_findings:
        return None

    lines = [
        "<details>",
        "<summary>Security review</summary>",
        "",
    ]
    for group in security_findings[:SECURITY_DETAILS_ROW_CAP]:
        file_suffix = f" (`{group.file_path}`)" if group.file_path else ""
        lines.append(f"- {_escape_markdown_inline(group.title)}{file_suffix}")
    if len(security_findings) > SECURITY_DETAILS_ROW_CAP:
        lines.append(
            f"- _{len(security_findings) - SECURITY_DETAILS_ROW_CAP} more security finding(s) "
            "in the findings table._"
        )
    lines.extend(["", "</details>"])
    return lines


def _important_files_details_lines(groups: list[GitHubFindingGroupORM]) -> list[str] | None:
    active = _active_groups(groups)
    if not active:
        return None

    rows: list[tuple[str, str]] = []
    seen_paths: set[str] = set()
    for group in _sorted_active_groups(groups):
        path = group.file_path or "—"
        if path in seen_paths:
            continue
        seen_paths.add(path)
        rows.append((path, group.title))
        if len(rows) >= IMPORTANT_FILES_ROW_CAP:
            break

    if not rows:
        return None

    lines = [
        "<details>",
        "<summary>Important files changed</summary>",
        "",
        "| File | Note |",
        "| --- | --- |",
    ]
    for path, note in rows:
        file_cell = _escape_markdown_table_cell(path) if path != "—" else "—"
        path_display = f"`{file_cell}`" if path != "—" else "—"
        lines.append(f"| {path_display} | {_escape_markdown_inline(note)} |")
    lines.extend(["", "</details>"])
    return lines


def _review_metadata_lines(ctx: PublishFormatContext) -> list[str]:
    return [
        "<details>",
        "<summary>Review metadata</summary>",
        "",
        f"- head_sha: `{ctx.head_sha}`",
        f"- revision: {ctx.revision_number}",
        "- trigger: autostart / `@revy review`",
        f"- [Open in Revy]({_revy_ui_link(ctx.pull_request_id)})",
        "",
        "</details>",
    ]


def build_pr_review_comment_fallback(
    ctx: PublishFormatContext,
    *,
    resolution_metrics_block: str | None = None,
) -> str:
    """Deterministic Greptile-shaped issue comment (G3 full narrative fallback)."""
    verdict = verdict_groups(ctx)
    pr_active = _active_groups(verdict)
    confidence = compute_publish_confidence(ctx)
    resolution_prose = _g9_resolution_prose_for_ctx(ctx)

    lines = [
        "## Revy code review",
        "",
        _review_narrative_paragraph(ctx),
        "",
        f"**Merge recommendation:** {_merge_recommendation(verdict)}",
        "",
        f"**Confidence score:** {confidence}/5",
        "",
        publish_confidence_rationale(ctx),
    ]

    if resolution_prose:
        lines.extend(["", f"**Since last push:** {resolution_prose}"])

    if resolution_metrics_block is None:
        resolution_metrics_block = _resolution_metrics_block(ctx)

    if resolution_metrics_block:
        lines.extend(["", resolution_metrics_block])

    attention = _files_needing_attention(verdict)
    if attention:
        lines.extend(["", "### Files needing attention", ""])
        lines.extend(f"- `{path}`" for path in attention)
    elif not pr_active:
        lines.extend(["", "No files require special attention on this revision."])

    lines.extend(
        [
            "",
            format_summary_comment(
                generation_groups=ctx.groups,
                pr_active_groups=verdict,
            ),
        ]
    )

    security_lines = _security_details_lines(verdict)
    if security_lines:
        lines.extend(["", *security_lines])

    important_files_lines = _important_files_details_lines(verdict)
    if important_files_lines:
        lines.extend(["", *important_files_lines])

    lines.extend(["", *_review_metadata_lines(ctx)])

    footer = _index_footer(ctx)
    if footer:
        lines.extend(["", footer])

    return "\n".join(lines)


def _confidence_rationale_snippet(normalized: str) -> str:
    """Slice after the confidence heading — stops at the next section."""
    lower = normalized.lower()
    conf_idx = lower.find("confidence")
    if conf_idx < 0:
        return lower
    tail = lower[conf_idx:]
    for end_marker in ("\n### ", "\n<details>", "\n---"):
        end_idx = tail.find(end_marker)
        if end_idx > 0:
            return tail[:end_idx]
    return tail[:400]


def _has_confidence_rationale_in_comment(normalized: str) -> bool:
    snippet = _confidence_rationale_snippet(normalized)
    return (
        "score is" in snippet
        or "confidence is" in snippet
        or ("because" in snippet and "/" in snippet)
        or "rationale" in snippet
    )


def _issue_comment_meets_product_bar(text: str, ctx: PublishFormatContext) -> bool:
    """Reject thin Moonshot markdown — deterministic fallback is the product minimum."""
    normalized = text.strip()
    if not normalized.startswith("## Revy code review"):
        return False
    if "**Confidence" not in normalized and "Confidence score" not in normalized:
        return False
    pr_active = _active_groups(verdict_groups(ctx))
    if not pr_active:
        return True
    has_merge_signal = "**Merge recommendation:**" in normalized
    has_rationale = _has_confidence_rationale_in_comment(normalized)
    has_table = "| Severity | Category | Title | File |" in normalized
    has_generation_block = "### This generation" in normalized
    has_pr_block = "### Still open on PR" in normalized
    if "### Findings" in normalized and not has_generation_block:
        return False
    return has_generation_block and has_pr_block and has_table and has_merge_signal and has_rationale


def _insert_resolution_metrics_block(text: str, ctx: PublishFormatContext) -> str:
    """Insert metrics after resolution prose — before files/findings/details (fallback parity)."""
    block = _resolution_metrics_block(ctx)
    if not block or block in text:
        return text
    for marker in (
        "### Files needing attention",
        "### This generation",
        "### Still open on PR",
        "### Findings",
        "<details>",
        "---\n*Review metadata",
    ):
        idx = text.find(marker)
        if idx >= 0:
            prefix = text[:idx].rstrip()
            suffix = text[idx:]
            return f"{prefix}\n\n{block}\n\n{suffix}"
    return f"{text}\n\n{block}"


def _append_resolution_metrics_block(text: str, ctx: PublishFormatContext) -> str:
    return _insert_resolution_metrics_block(text, ctx)


def _findings_payload(groups: list[GitHubFindingGroupORM]) -> list[dict[str, str | None]]:
    return [
        {
            "severity": stored_enum_value(group.severity),
            "category": stored_enum_value(group.category),
            "title": group.title,
            "file": group.file_path,
        }
        for group in _active_groups(groups)[:SUMMARY_ROW_CAP]
    ]


def _build_issue_comment_user_prompt(ctx: PublishFormatContext) -> str:
    verdict = verdict_groups(ctx)
    generation_active = _active_groups(ctx.groups)
    pr_active = _active_groups(verdict)
    confidence = compute_publish_confidence(ctx)
    has_security = any(group.category == FindingCategory.security for group in pr_active)
    return (
        "Format the issue comment from this structured review context.\n\n"
        f"PR #{ctx.pull_request_number} revision {ctx.revision_number} head_sha={ctx.head_sha}\n"
        f"Confidence score (use this exact value): {confidence}/5\n"
        f"Label the section **Confidence score:** {confidence}/5 in the comment.\n"
        f"Confidence rationale (include as one sentence after the score): "
        f"{publish_confidence_rationale(ctx)}\n"
        f"Narrative hints (write 2-4 sentences in your own words): "
        f"{_review_narrative_paragraph(ctx)}\n"
        f"Merge recommendation (use this exact line): {_merge_recommendation(verdict)}\n"
        f"Resolution delta: {_g9_resolution_prose_for_ctx(ctx) or 'n/a'}\n"
        "Findings layout: use ### This generation and ### Still open on PR markdown "
        "headings with severity tables (no ### Findings section).\n"
        f"Include security <details> block: {'yes' if has_security else 'no'}\n"
        f"Include important files changed <details> table when findings exist.\n"
        f"This-generation active findings JSON: "
        f"{json.dumps(_findings_payload(ctx.groups), ensure_ascii=False)}\n"
        f"PR-wide still-open findings JSON: "
        f"{json.dumps(_findings_payload(verdict), ensure_ascii=False)}\n"
        f"Generation active count: {len(generation_active)}; PR active count: {len(pr_active)}"
    )


async def build_pr_review_comment(ctx: PublishFormatContext) -> str:
    """Full issue comment via Moonshot when configured; table fallback on failure (G5)."""
    fallback = build_pr_review_comment_fallback(ctx)
    if not settings.reviewer_llm_enabled():
        return fallback

    prompt = _build_issue_comment_user_prompt(ctx)

    try:
        async with httpx.AsyncClient(
            timeout=float(settings.revy_revision_timeout_standard_seconds)
        ) as client:
            raw = await moonshot_review.complete_issue_comment_markdown(
                client,
                profile="standard",
                user_prompt=prompt,
                model_id=settings.revy_moonshot_model_for_profile("standard"),
            )
        text = normalize_llm_issue_comment(raw)
        if not text or _looks_like_json_wrapper(text):
            logger.warning(
                "github_publish_formatter_llm_unparsed_markdown",
                extra={
                    "pull_request_id": str(ctx.pull_request_id),
                    "raw_prefix": raw.strip()[:200],
                },
            )
            return fallback
        if not _issue_comment_meets_product_bar(text, ctx):
            logger.warning(
                "github_publish_formatter_llm_thin_markdown",
                extra={
                    "pull_request_id": str(ctx.pull_request_id),
                    "raw_prefix": text.strip()[:200],
                },
            )
            return fallback
        footer = _index_footer(ctx)
        if footer and footer not in text:
            text = f"{text}\n\n{footer}"
        return _append_resolution_metrics_block(text, ctx)
    except (httpx.HTTPError, ValueError, OSError, ServiceUnavailableError) as exc:
        logger.warning(
            "github_publish_formatter_llm_failed",
            extra={"pull_request_id": str(ctx.pull_request_id), "error": str(exc)},
        )

    return fallback


def _build_summary_json(ctx: PublishFormatContext) -> dict:
    verdict = verdict_groups(ctx)
    confidence = compute_publish_confidence(ctx)
    if ctx.resolution_metrics_manifest is not None:
        resolution = resolution_counts_from_manifest(ctx.resolution_metrics_manifest)
    else:
        resolution = count_resolution_status(ctx.groups)
    return {
        "head_sha": ctx.head_sha,
        "revision_number": ctx.revision_number,
        "confidence": confidence,
        "active_count": len(_active_groups(verdict)),
        "generation_active_count": len(_active_groups(ctx.groups)),
        "pr_active_count": len(_active_groups(verdict)),
        "resolution": resolution,
    }


def build_publish_format_result(ctx: PublishFormatContext) -> PublishFormatResult:
    check_summary = build_check_run_summary(ctx)
    issue_comment = build_pr_review_comment_fallback(ctx)
    summary_json = _build_summary_json(ctx)
    return PublishFormatResult(
        check_summary=check_summary,
        issue_comment=issue_comment,
        confidence=summary_json["confidence"],
        summary_json=summary_json,
    )


async def build_publish_format_result_async(ctx: PublishFormatContext) -> PublishFormatResult:
    check_summary = build_check_run_summary(ctx)
    issue_comment = await build_pr_review_comment(ctx)
    summary_json = _build_summary_json(ctx)
    return PublishFormatResult(
        check_summary=check_summary,
        issue_comment=issue_comment,
        confidence=summary_json["confidence"],
        summary_json=summary_json,
    )
