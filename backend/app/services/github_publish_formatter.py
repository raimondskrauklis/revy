# backend/app/services/github_publish_formatter.py
"""Greptile-shaped GitHub publish formatting — RQ7."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from uuid import UUID

import httpx

from app.constants.enums import (
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubIndexMode,
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
    return isinstance(payload, dict)


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
        ResolutionStatus.still_open.value: 0,
    }
    for group in groups:
        if group.resolution_status is None:
            continue
        if group.state == GitHubFindingGroupState.resolved:
            counts[ResolutionStatus.judge_dismissed.value] += 1
            continue
        if group.resolution_status == ResolutionStatus.addressed:
            if group.state != GitHubFindingGroupState.active:
                counts[ResolutionStatus.addressed.value] += 1
            continue
        if (
            group.resolution_status == ResolutionStatus.still_open
            and group.state == GitHubFindingGroupState.active
        ):
            counts[ResolutionStatus.still_open.value] += 1
    return counts


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
    score += min(1, resolution[ResolutionStatus.judge_dismissed.value])
    return max(0, min(5, score))


def build_g9_resolution_prose(groups: list[GitHubFindingGroupORM]) -> str:
    counts = count_resolution_status(groups)
    parts: list[str] = []
    if counts[ResolutionStatus.addressed.value]:
        n = counts[ResolutionStatus.addressed.value]
        parts.append(f"{n} issue{'s' if n != 1 else ''} fixed since last push")
    if counts[ResolutionStatus.judge_dismissed.value]:
        n = counts[ResolutionStatus.judge_dismissed.value]
        parts.append(f"{n} dismissed by judge")
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


def build_check_run_summary(ctx: PublishFormatContext) -> str:
    """G3 compact body for GitHub check run output."""
    active = _active_groups(ctx.groups)
    confidence = compute_confidence(ctx.groups)
    lines = [
        "## Revy review",
        "",
        f"**Confidence:** {confidence}/5",
        "",
    ]
    if not active:
        lines.append("No files require special attention.")
        return "\n".join(lines)

    lines.extend(_severity_table_rows(ctx.groups))
    if len(active) > SUMMARY_ROW_CAP:
        lines.extend(["", f"_Showing {SUMMARY_ROW_CAP} of {len(active)} findings._"])
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


def build_pr_review_comment_fallback(ctx: PublishFormatContext) -> str:
    """Deterministic Greptile-shaped issue comment (G3 full narrative fallback)."""
    active = _active_groups(ctx.groups)
    confidence = compute_confidence(ctx.groups)
    resolution_prose = build_g9_resolution_prose(ctx.groups)

    lines = [
        "## Revy code review",
        "",
        f"**Confidence score:** {confidence}/5",
        "",
    ]

    if not active:
        lines.append("No files require special attention on this revision.")
    else:
        lines.append(
            f"Found **{len(active)}** active finding{'s' if len(active) != 1 else ''} "
            f"on revision {ctx.revision_number}."
        )

    if resolution_prose:
        lines.extend(["", f"**Since last push:** {resolution_prose}"])

    attention = _files_needing_attention(ctx.groups)
    if attention:
        lines.extend(["", "### Files needing attention", ""])
        lines.extend(f"- `{path}`" for path in attention)

    if active:
        lines.extend(["", "### Findings", ""])
        lines.extend(_severity_table_rows(ctx.groups))
        if len(active) > SUMMARY_ROW_CAP:
            lines.append("")
            lines.append(f"_Showing {SUMMARY_ROW_CAP} of {len(active)} findings._")

    lines.extend(
        [
            "",
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
    )

    footer = _index_footer(ctx)
    if footer:
        lines.extend(["", footer])

    return "\n".join(lines)


async def build_pr_review_comment(ctx: PublishFormatContext) -> str:
    """Full issue comment via Moonshot when configured; table fallback on failure (G5)."""
    fallback = build_pr_review_comment_fallback(ctx)
    if not settings.reviewer_llm_enabled():
        return fallback

    active = _active_groups(ctx.groups)
    prompt = (
        "Format the issue comment from this structured review context.\n\n"
        f"PR #{ctx.pull_request_number} revision {ctx.revision_number} head_sha={ctx.head_sha}\n"
        f"Confidence (use this value): {compute_confidence(ctx.groups)}/5\n"
        f"Resolution delta: {build_g9_resolution_prose(ctx.groups) or 'n/a'}\n"
        f"Active findings JSON: "
        f"{[{'severity': stored_enum_value(g.severity), 'category': stored_enum_value(g.category), 'title': g.title, 'file': g.file_path} for g in active[:SUMMARY_ROW_CAP]]}"
    )

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
        return text
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
