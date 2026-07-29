# backend/app/services/github_publish_formatter.py
"""Greptile-shaped GitHub publish formatting — RQ7."""
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
SUMMARY_ROW_CAP = 50

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


def compute_confidence(groups: list[GitHubFindingGroupORM]) -> int:
    active = [g for g in groups if g.state == GitHubFindingGroupState.active]
    if not active:
        return 5

    score = 5
    if any(g.severity in (FindingSeverity.critical, FindingSeverity.error) for g in active):
        score -= 2
    elif any(g.severity == FindingSeverity.warning for g in active):
        score -= 1

    resolution = count_resolution_status(groups)
    score += min(2, resolution[ResolutionStatus.addressed.value])
    dismissed_total = (
        resolution[ResolutionStatus.judge_dismissed.value]
        + resolution[ResolutionMethod.verification_dismissed.value]
        + resolution[ResolutionMethod.human_dismissed.value]
    )
    score += min(1, dismissed_total)
    return max(0, min(5, score))


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


def _active_groups(groups: list[GitHubFindingGroupORM]) -> list[GitHubFindingGroupORM]:
    return [g for g in groups if g.state == GitHubFindingGroupState.active]


def _severity_table_rows(groups: list[GitHubFindingGroupORM]) -> list[str]:
    active = _active_groups(groups)[:SUMMARY_ROW_CAP]
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
    confidence = compute_confidence(ctx.groups)
    pr_active = ctx.pr_active_groups if ctx.pr_active_groups is not None else ctx.groups
    lines = [
        "## Revy review",
        "",
        f"**Confidence:** {confidence}/5",
        "",
        format_summary_comment(
            generation_groups=ctx.groups,
            pr_active_groups=pr_active,
        ),
    ]
    return "\n".join(lines)


def _files_needing_attention(groups: list[GitHubFindingGroupORM]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for group in _active_groups(groups):
        if not group.file_path or group.file_path in seen:
            continue
        seen.add(group.file_path)
        paths.append(group.file_path)
        if len(paths) >= FILES_NEEDING_ATTENTION_CAP:
            break
    return paths


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


def _confidence_rationale(groups: list[GitHubFindingGroupORM]) -> str:
    active = _active_groups(groups)
    confidence = compute_confidence(groups)
    if not active:
        return "Score is 5 because there are no active findings on this revision."
    if confidence <= 2:
        return "Score is low due to critical or error-severity findings that need attention before merge."
    if confidence == 3:
        return "Score is moderated by active findings that still need review before merge."
    if confidence == 4:
        return (
            "Score is good but not perfect: some active findings remain, "
            "though prior fixes or dismissals improved confidence."
        )
    return "Score is high with only informational findings or strong resolution progress on this revision."


def _review_narrative_paragraph(ctx: PublishFormatContext) -> str:
    active = _active_groups(ctx.groups)
    if not active:
        return (
            "This revision completed without active findings that need follow-up. "
            "No merge blockers were identified from the automated review on this push."
        )

    severity_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for group in active:
        severity = stored_enum_value(group.severity)
        category = stored_enum_value(group.category)
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1

    dominant_category = max(category_counts, key=category_counts.get)
    severity_mix = ", ".join(f"{count} {name}" for name, count in sorted(severity_counts.items()))
    sentences = [
        (
            f"This revision has **{len(active)}** active finding"
            f"{'s' if len(active) != 1 else ''} on PR #{ctx.pull_request_number} "
            f"(revision {ctx.revision_number})."
        ),
        f"Severity mix: {severity_mix}.",
        f"The dominant theme is **{dominant_category}**-related feedback.",
    ]
    if any(g.severity in (FindingSeverity.critical, FindingSeverity.error) for g in active):
        sentences.append("Address critical or error findings before merge.")
    elif severity_counts.get(FindingSeverity.warning.value, 0):
        sentences.append("Review warnings before merge; no critical blockers were flagged.")
    else:
        sentences.append("Findings are informational; merge risk appears low pending your judgment.")
    return " ".join(sentences)


def _security_details_lines(groups: list[GitHubFindingGroupORM]) -> list[str] | None:
    security_findings = [
        group for group in _active_groups(groups) if group.category == FindingCategory.security
    ]
    if not security_findings:
        return None

    lines = [
        "<details>",
        "<summary>Security review</summary>",
        "",
    ]
    for group in security_findings:
        file_suffix = f" (`{group.file_path}`)" if group.file_path else ""
        lines.append(f"- {_escape_markdown_table_cell(group.title)}{file_suffix}")
    lines.extend(["", "</details>"])
    return lines


def _important_files_details_lines(groups: list[GitHubFindingGroupORM]) -> list[str] | None:
    active = _active_groups(groups)
    if not active:
        return None

    rows: list[tuple[str, str]] = []
    seen_paths: set[str] = set()
    for group in active:
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
        lines.append(f"| {path_display} | {_escape_markdown_table_cell(note)} |")
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
    active = _active_groups(ctx.groups)
    confidence = compute_confidence(ctx.groups)
    resolution_prose = build_g9_resolution_prose(ctx.groups)

    lines = [
        "## Revy code review",
        "",
        _review_narrative_paragraph(ctx),
        "",
        f"**Confidence score:** {confidence}/5",
        "",
        _confidence_rationale(ctx.groups),
    ]

    if resolution_prose:
        lines.extend(["", f"**Since last push:** {resolution_prose}"])

    if resolution_metrics_block is None:
        resolution_metrics_block = _resolution_metrics_block(ctx)

    if resolution_metrics_block:
        lines.extend(["", resolution_metrics_block])

    attention = _files_needing_attention(ctx.groups)
    if attention:
        lines.extend(["", "### Files needing attention", ""])
        lines.extend(f"- `{path}`" for path in attention)
    elif not active:
        lines.extend(["", "No files require special attention on this revision."])

    if active:
        lines.extend(["", "### Findings", ""])
        lines.extend(_severity_table_rows(ctx.groups))
        if len(active) > SUMMARY_ROW_CAP:
            lines.append("")
            lines.append(f"_Showing {SUMMARY_ROW_CAP} of {len(active)} findings._")

    security_lines = _security_details_lines(ctx.groups)
    if security_lines:
        lines.extend(["", *security_lines])

    important_files_lines = _important_files_details_lines(ctx.groups)
    if important_files_lines:
        lines.extend(["", *important_files_lines])

    lines.extend(["", *_review_metadata_lines(ctx)])

    footer = _index_footer(ctx)
    if footer:
        lines.extend(["", footer])

    return "\n".join(lines)


def _append_resolution_metrics_block(text: str, ctx: PublishFormatContext) -> str:
    block = _resolution_metrics_block(ctx)
    if block and block not in text:
        return f"{text}\n\n{block}"
    return text


def _build_issue_comment_user_prompt(ctx: PublishFormatContext) -> str:
    active = _active_groups(ctx.groups)
    confidence = compute_confidence(ctx.groups)
    findings_payload = [
        {
            "severity": stored_enum_value(group.severity),
            "category": stored_enum_value(group.category),
            "title": group.title,
            "file": group.file_path,
        }
        for group in active[:SUMMARY_ROW_CAP]
    ]
    has_security = any(group.category == FindingCategory.security for group in active)
    return (
        "Format the issue comment from this structured review context.\n\n"
        f"PR #{ctx.pull_request_number} revision {ctx.revision_number} head_sha={ctx.head_sha}\n"
        f"Confidence (use this exact value): {confidence}/5\n"
        f"Confidence rationale (include as one sentence after the score): "
        f"{_confidence_rationale(ctx.groups)}\n"
        f"Narrative hints (write 2-4 sentences in your own words): "
        f"{_review_narrative_paragraph(ctx)}\n"
        f"Resolution delta: {build_g9_resolution_prose(ctx.groups) or 'n/a'}\n"
        f"Include security <details> block: {'yes' if has_security else 'no'}\n"
        f"Include important files changed <details> table when findings exist.\n"
        f"Active findings JSON: {findings_payload}"
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


def build_publish_format_result(ctx: PublishFormatContext) -> PublishFormatResult:
    check_summary = build_check_run_summary(ctx)
    issue_comment = build_pr_review_comment_fallback(ctx)
    confidence = compute_confidence(ctx.groups)
    return PublishFormatResult(
        check_summary=check_summary,
        issue_comment=issue_comment,
        confidence=confidence,
        summary_json={
            "head_sha": ctx.head_sha,
            "revision_number": ctx.revision_number,
            "confidence": confidence,
            "active_count": len(_active_groups(ctx.groups)),
            "resolution": count_resolution_status(ctx.groups),
        },
    )


async def build_publish_format_result_async(ctx: PublishFormatContext) -> PublishFormatResult:
    check_summary = build_check_run_summary(ctx)
    issue_comment = await build_pr_review_comment(ctx)
    confidence = compute_confidence(ctx.groups)
    return PublishFormatResult(
        check_summary=check_summary,
        issue_comment=issue_comment,
        confidence=confidence,
        summary_json={
            "head_sha": ctx.head_sha,
            "revision_number": ctx.revision_number,
            "confidence": confidence,
            "active_count": len(_active_groups(ctx.groups)),
            "resolution": count_resolution_status(ctx.groups),
        },
    )
