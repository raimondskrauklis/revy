# backend/app/services/github_publish_formatter.py
"""Greptile-shaped GitHub publish formatting — RQ7 + PSA two-block parity.

Surface contract (PSA-D1–D4, PSA-D12):
- Check + issue comment share ``format_summary_comment`` (this generation + still open on PR).
- Verdict fields (confidence, merge, rationale, files, security rollups) use PR-wide active groups.
- ``filter_pr_active_groups_for_summary`` drops groups whose inline thread is collapsed (GH-1v2) and
  summary-only orphans (never inlined, not in this generation) so ``### Still open on PR`` matches
  visible GitHub threads.
- Verdict confidence applies generation resolution boost from ``ctx.groups`` (PSA-D3).
- G9 / resolution metrics: this-push deltas stay generation-scoped in the manifest; displayed
  ``still_open`` count uses ``display_still_open_prior_count`` so metrics match filtered
  ``### Still open on PR`` rows (SOS-5).
- Inline publish remains generation-only; ``compute_check_conclusion`` unchanged (generation-scoped).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from uuid import UUID

import httpx

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubIndexMode,
    LlmCallOperationName,
    LlmCallStepType,
    ResolutionMethod,
    ResolutionStatus,
    stored_enum_value,
)
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.core.logging import get_logger
from app.integrations import moonshot_review
from app.models.github_finding_group import GitHubFindingGroupORM
from app.services.llm_call_recorder import LlmAttemptStartContext

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
    ever_inlined_fingerprints: frozenset[str] | None = None
    pr_resolution_rollup: dict[str, object] | None = None
    pipeline_run_id: UUID | None = None
    review_run_id: UUID | None = None


@dataclass(frozen=True)
class PublishFormatResult:
    check_summary: str
    issue_comment: str
    confidence: int
    summary_json: dict
    publish_model_provider: str | None = None
    publish_model_id: str | None = None


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


def format_resolution_metrics_block(
    manifest: dict[str, object],
    *,
    display_still_open_prior: int | None = None,
) -> str:
    """FR-Q12 transitions block from reconcile manifest resolution_pass."""
    addressed = int(manifest.get("transitions_addressed") or 0)
    dismissed = manifest.get("transitions_dismissed", {})
    manifest_still_open = int(manifest.get("still_open_count") or 0)
    still_open = (
        display_still_open_prior
        if display_still_open_prior is not None
        else manifest_still_open
    )
    denominator = int(manifest.get("denominator_active_prior") or 0)
    transition_count = int(manifest.get("transition_count") or 0)
    compare_failed = int(manifest.get("compare_failed_count") or 0)
    rate = manifest.get("resolution_rate_pct", 0.0)
    if (
        display_still_open_prior is not None
        and display_still_open_prior != manifest_still_open
    ):
        hidden_still_open = max(manifest_still_open - display_still_open_prior, 0)
        denominator = max(denominator - hidden_still_open, 0)
        rate = round((transition_count / denominator) * 100, 1) if denominator else 0.0

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
        f"- **Resolution rate:** {rate}% ({transition_count}/{denominator} prior active)",
        f"- **Closed as fixed:** {addressed}",
    ]
    if dismissed_parts:
        lines.append(f"- **Dismissed:** {', '.join(dismissed_parts)}")
    if isinstance(still_open, int) and still_open > 0:
        lines.append(f"- **Still open from prior review:** {still_open}")
    if isinstance(compare_failed, int) and compare_failed > 0:
        lines.append(f"- **Compare blocked:** {compare_failed} group(s)")
    hygiene_path_removed = manifest.get("hygiene_path_removed_count")
    if isinstance(hygiene_path_removed, int) and hygiene_path_removed > 0:
        lines.append(
            f"- **Closed as path removed:** {hygiene_path_removed} (outside this push pair)"
        )
    head_check_failed = manifest.get("head_check_failed_count")
    if isinstance(head_check_failed, int) and head_check_failed > 0:
        lines.append(f"- **HEAD path check blocked:** {head_check_failed} group(s)")
    return "\n".join(lines)


def format_thread_resolve_skipped_block(skipped: dict[str, int]) -> str | None:
    """RR-W1 R2 — operator-visible thread resolve skip breakdown."""
    parts: list[str] = []
    labels = (
        ("thread_id_not_found", "thread_id_not_found"),
        ("resolve_mutation_failed", "resolve_mutation_failed"),
        ("already_resolved", "already_resolved"),
        ("thread_not_revy_owned", "thread_not_revy_owned"),
    )
    total = 0
    for key, label in labels:
        count = skipped.get(key, 0)
        if isinstance(count, int) and count > 0:
            parts.append(f"{label}: {count}")
            total += count
    if total == 0:
        return None
    breakdown = ", ".join(parts)
    return f"- **Thread resolve skipped:** {total} ({breakdown})"


def append_thread_resolve_skipped_block(text: str, skipped: dict[str, int]) -> str:
    block = format_thread_resolve_skipped_block(skipped)
    if block is None:
        return text
    return f"{text.rstrip()}\n\n{block}"


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


def build_g9_resolution_prose_from_manifest(
    manifest: dict[str, object],
    *,
    display_still_open_prior: int | None = None,
) -> str:
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
    still_open = (
        display_still_open_prior
        if display_still_open_prior is not None
        else int(manifest.get("still_open_count") or 0)
    )
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
    display_still_open = display_still_open_prior_count(ctx)
    if ctx.resolution_metrics_manifest is not None:
        return build_g9_resolution_prose_from_manifest(
            ctx.resolution_metrics_manifest,
            display_still_open_prior=display_still_open,
        )
    return build_g9_resolution_prose(ctx.groups)


def _active_groups(groups: list[GitHubFindingGroupORM]) -> list[GitHubFindingGroupORM]:
    return [g for g in groups if g.state == GitHubFindingGroupState.active]


def filter_pr_active_groups_for_summary(
    groups: list[GitHubFindingGroupORM],
    *,
    publishable_fingerprints: set[str],
    collapsed_fingerprints: set[str],
    generation_fingerprints: set[str] | None = None,
    ever_inlined_fingerprints: set[str] | None = None,
) -> list[GitHubFindingGroupORM]:
    """PR-wide still-open rows aligned with GH-1v2 inline thread collapse.

    Active groups whose fingerprint was successfully collapsed on GitHub and is
    absent from this generation's publishable set should not appear as still open.
    Generation-scoped groups stay visible even when judge-gated off inline publish.
    Summary-only orphans (never received an inline comment, not in this generation)
    are omitted so block 2 matches visible GitHub threads (SOS-5).
    """
    filtered: list[GitHubFindingGroupORM] = []
    for group in groups:
        if group.resolution_status == ResolutionStatus.addressed:
            continue
        if (
            group.fingerprint in collapsed_fingerprints
            and group.fingerprint not in publishable_fingerprints
            and (
                generation_fingerprints is None
                or group.fingerprint not in generation_fingerprints
            )
        ):
            continue
        if (
            ever_inlined_fingerprints is not None
            and generation_fingerprints is not None
            and group.fingerprint not in ever_inlined_fingerprints
            and group.fingerprint not in generation_fingerprints
        ):
            continue
        filtered.append(group)
    return filtered


def display_still_open_prior_count(ctx: PublishFormatContext) -> int:
    """Prior-revision actives visible on the publish surface (post summary filters)."""
    generation_fingerprints = {group.fingerprint for group in ctx.groups}
    return sum(
        1
        for group in _active_groups(verdict_groups(ctx))
        if group.fingerprint not in generation_fingerprints
    )


_PR_SUMMARY_HEADING = "### PR summary (lifetime)"
_PR_SUMMARY_DETAILS_SUMMARY = "Lifetime breakdown"
_PR_SUMMARY_SECTION_END_MARKERS = (
    "\n\n**Since last push:**",
    "\n### Resolution metrics",
    "\n### Files needing attention",
    "\n### This generation",
)
_RESOLVED_METHOD_LABELS = (
    ("absent_and_addressed", "addressed"),
    ("judge_dismissed", "judge dismissed"),
    ("verification_dismissed", "verification dismissed"),
    ("human_dismissed", "human dismissed"),
    ("path_removed", "path removed"),
)


_HIDDEN_FILTER_KEYS = (
    ("collapsed_hidden", "collapsed inline threads"),
    ("orphan_never_inlined_hidden", "never-inlined summary-only"),
    ("compare_failed_hidden", "compare/closure blocked"),
)


def _safe_snapshot_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def _hidden_total_from_filter_snapshot(filter_snapshot: object) -> int:
    if not isinstance(filter_snapshot, dict):
        return 0
    return sum(
        _safe_snapshot_int(filter_snapshot.get(key)) for key, _ in _HIDDEN_FILTER_KEYS
    )


def _optional_lifetime_rate_pct(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _canonical_newlines(markdown: str) -> str:
    return markdown.replace("\r\n", "\n").replace("\r", "\n")


def _heading_suffix_matches(remainder: str, suffix: str) -> bool:
    if not remainder.startswith(suffix):
        return False
    after = remainder[len(suffix) :]
    return not after or after[0] in "\n\r"


def _find_splice_marker(
    markdown: str,
    marker: str,
    start: int = 0,
    *,
    heading_suffixes: tuple[str, ...] = (),
) -> int:
    """Find marker at line start; heading markers must not prefix a longer heading."""
    require_heading_eol = marker.startswith("###")
    while True:
        idx = markdown.find(marker, start)
        if idx < 0:
            return -1
        if idx > 0 and markdown[idx - 1] not in "\n\r":
            start = idx + 1
            continue
        if require_heading_eol:
            end = idx + len(marker)
            remainder = markdown[end:]
            if (
                remainder
                and remainder[0] not in "\n\r"
                and not any(
                    _heading_suffix_matches(remainder, suffix)
                    for suffix in heading_suffixes
                )
            ):
                start = idx + 1
                continue
        return idx


def _section_end_marker_matches(tail: str, index: int, marker: str) -> bool:
    if not tail.startswith(marker, index):
        return False
    end = index + len(marker)
    if end >= len(tail):
        return True
    next_char = tail[end]
    if marker.endswith("**Since last push:**"):
        return True
    if marker == "\n### Resolution metrics":
        if next_char in "\n\r":
            return True
        return _heading_suffix_matches(tail[end:], " (this push)")
    if marker in ("\n### Files needing attention", "\n### This generation"):
        return next_char in "\n\r"
    return next_char in "\n\r"


def _at_line_start(text: str, index: int) -> bool:
    return index <= 0 or text[index - 1] in "\n\r"


def _pr_summary_section_end_offset(tail: str) -> int:
    """Offset where lifetime block ends; ignores markers inside <details> or fences."""
    footer_idx = _find_review_footer_insert_index(tail)
    details_depth = 0
    fence_depth = 0
    tail_lower = tail.lower()
    i = 0
    while i < len(tail):
        if fence_depth == 0 and details_depth == 0:
            for marker in _PR_SUMMARY_SECTION_END_MARKERS:
                if _section_end_marker_matches(tail, i, marker):
                    if footer_idx >= 0:
                        return min(i, footer_idx)
                    return i
        if _at_line_start(tail, i) and tail.startswith("```", i):
            line_end = tail.find("\n", i)
            if line_end < 0:
                line_end = len(tail)
            if tail[i:line_end].strip().startswith("```"):
                fence_depth ^= 1
                i = line_end
                continue
        if fence_depth == 0:
            if tail_lower.startswith("<details", i):
                gt = tail.find(">", i)
                if gt < 0:
                    i += 1
                    continue
                details_depth += 1
                i = gt + 1
                continue
            if tail_lower.startswith("</details>", i):
                details_depth = max(0, details_depth - 1)
                i += len("</details>")
                continue
        i += 1
    if footer_idx >= 0:
        return footer_idx
    return len(tail)


def _format_publishable_status_line(*, still_open: int, hidden_total: int) -> str:
    if still_open > 0:
        return (
            f"**Publishable status:** {still_open} open — see Still open on PR"
        )
    if hidden_total > 0:
        return (
            "**Publishable status:** Nothing to act on in the tables below "
            f"({hidden_total} hidden from display — expand breakdown)."
        )
    return "**Publishable status:** Nothing to act on in the tables below."


def _format_pr_summary_details_block(
    rollup: dict[str, object],
    *,
    raised: int,
    resolved: int,
    still_open: int,
    hidden_total: int,
) -> list[str]:
    lines: list[str] = []
    by_method = rollup.get("resolved_by_method")
    if isinstance(by_method, dict) and resolved > 0:
        lines.append("**Resolved (lifetime)**")
        for key, label in _RESOLVED_METHOD_LABELS:
            count = int(by_method.get(key) or 0)
            if count:
                lines.append(f"- {label}: {count}")
        lines.append("")

    filter_snapshot = rollup.get("filter_snapshot")
    if hidden_total > 0 and isinstance(filter_snapshot, dict):
        lines.append("**Hidden from tables** (no open GitHub thread to act on)")
        for key, label in _HIDDEN_FILTER_KEYS:
            count = _safe_snapshot_int(filter_snapshot.get(key))
            if count:
                lines.append(f"- {label}: {count}")
        lines.append("")

    if (
        isinstance(filter_snapshot, dict)
        and raised == resolved + still_open + hidden_total
    ):
        lines.append(
            f"Reconciliation: raised ({raised}) = resolved ({resolved}) + "
            f"display open ({still_open}) + hidden ({hidden_total})."
        )
    elif isinstance(filter_snapshot, dict):
        raw_active = _safe_snapshot_int(filter_snapshot.get("raw_active_before_filters"))
        lines.append(
            f"Reconciliation: {raised} raised; {resolved} resolved; "
            f"{still_open} display open; {hidden_total} hidden."
        )
        if raw_active:
            lines.append(
                f"Raw active before display filters: {raw_active} "
                "(may include addressed-pending groups)."
            )

    still_open_prior = int(rollup.get("still_open_prior") or 0)
    if still_open_prior != still_open:
        lines.append(
            "Push metrics may show a different prior-open count — push block uses "
            "prior-revision pairing; tables use display-filtered counts."
        )

    rate = _optional_lifetime_rate_pct(rollup.get("lifetime_resolution_rate_pct"))
    if rate is not None:
        lines.append(
            f"Lifetime resolution rate ({rate}%) uses display open only, not raw DB active count."
        )
    elif resolved + still_open == 0:
        lines.append("Lifetime resolution rate: N/A (no resolved or display-open groups).")

    return lines


def format_pr_resolution_rollup_block(rollup: dict[str, object]) -> str:
    """Lifetime PR rollup markdown block (PSR P1 + P4 scan/details)."""
    raised = int(rollup.get("raised_count") or 0)
    resolved = int(rollup.get("resolved_count") or 0)
    still_open = int(rollup.get("still_open_display") or 0)
    filter_snapshot = rollup.get("filter_snapshot")
    hidden_total = _hidden_total_from_filter_snapshot(filter_snapshot)

    lines = [
        _PR_SUMMARY_HEADING,
        "",
        _format_publishable_status_line(still_open=still_open, hidden_total=hidden_total),
        "",
        "| | Count |",
        "|--|--:|",
        f"| Raised on this PR | {raised} |",
        f"| Resolved (lifetime) | {resolved} |",
        f"| Still open (in tables) | {still_open} |",
    ]
    if hidden_total > 0:
        lines.append(f"| Hidden from tables | {hidden_total} |")

    disclosure = rollup.get("lifetime_disclosure")
    if isinstance(disclosure, str) and disclosure.strip():
        lines.extend(["", disclosure.strip()])

    detail_lines = _format_pr_summary_details_block(
        rollup,
        raised=raised,
        resolved=resolved,
        still_open=still_open,
        hidden_total=hidden_total,
    )
    if detail_lines:
        lines.extend(
            [
                "",
                "<details>",
                f"<summary>{_PR_SUMMARY_DETAILS_SUMMARY}</summary>",
                "",
                *detail_lines,
                "</details>",
            ]
        )

    return "\n".join(lines)


_REVIEW_METADATA_SUMMARY = "<summary>Review metadata</summary>"


def _review_metadata_details_is_footer(block: str) -> bool:
    if "Revision:" in block or "Head:" in block:
        return True
    if "head_sha" in block or "revision_number" in block:
        return True
    after_summary = block.split("</summary>", 1)[-1].replace("</details>", "").strip()
    return not after_summary


def _find_valid_review_metadata_details_index(text: str) -> int:
    search_from = len(text)
    while search_from > 0:
        summary_idx = text.rfind(_REVIEW_METADATA_SUMMARY, 0, search_from)
        if summary_idx < 0:
            return -1
        start = text.rfind("<details>", 0, summary_idx)
        close = text.find("</details>", summary_idx)
        if start >= 0 and close >= 0:
            block = text[start : close + len("</details>")]
            if _review_metadata_details_is_footer(block):
                return start
        search_from = summary_idx
    return -1


def _find_review_footer_insert_index(markdown: str) -> int:
    """Index before rollup metadata footer (validated --- block or Review metadata details)."""
    text = _canonical_newlines(markdown)
    candidates: list[int] = []
    details_idx = _find_valid_review_metadata_details_index(text)
    if details_idx >= 0:
        candidates.append(details_idx)
    footer_marker = "\n---\n*"
    footer_idx = text.rfind(footer_marker)
    if footer_idx >= 0:
        tail = text[footer_idx:]
        if "Revision:" in tail and tail.rstrip().endswith("*"):
            candidates.append(footer_idx)
    return min(candidates) if candidates else -1


def _replace_pr_summary_section(markdown: str, new_block: str) -> str:
    """Replace PR summary section without truncating inner <details> in the rollup block."""
    markdown = _canonical_newlines(markdown)
    start = _find_splice_marker(markdown, _PR_SUMMARY_HEADING)
    if start < 0:
        return markdown
    end = start + len(_PR_SUMMARY_HEADING)
    tail = markdown[end:]
    end_offset = _pr_summary_section_end_offset(tail)
    return markdown[:start] + new_block.rstrip() + tail[end_offset:]


def format_pr_rollup_check_one_liner(rollup: dict[str, object]) -> str:
    resolved = int(rollup.get("resolved_count") or 0)
    raised = int(rollup.get("raised_count") or 0)
    still_open = int(rollup.get("still_open_display") or 0)
    return (
        f"**PR (lifetime):** {resolved} resolved / {raised} raised; "
        f"{still_open} still open"
    )


def format_push_delta_check_one_liner(ctx: PublishFormatContext) -> str:
    prose = _g9_resolution_prose_for_ctx(ctx)
    if not prose:
        if ctx.revision_number <= 1:
            return "**This push:** first review on this PR"
        return "**This push:** no resolution transitions"
    return f"**This push:** {prose}"


def splice_deterministic_pr_summary_block(markdown: str, ctx: PublishFormatContext) -> str:
    """Insert or replace deterministic PR lifetime summary before push delta sections."""
    rollup = ctx.pr_resolution_rollup
    if not isinstance(rollup, dict):
        return markdown
    markdown = _canonical_newlines(markdown)
    block = format_pr_resolution_rollup_block(rollup)
    if _find_splice_marker(markdown, _PR_SUMMARY_HEADING) >= 0:
        return _replace_pr_summary_section(markdown, block)
    for marker in ("**Since last push:**",):
        idx = _find_splice_marker(markdown, marker)
        if idx >= 0:
            prefix = markdown[:idx].rstrip()
            suffix = markdown[idx:]
            return f"{prefix}\n\n{block}\n\n{suffix}"
    for marker in ("### Resolution metrics (this push)", "### Resolution metrics"):
        idx = _find_splice_marker(
            markdown,
            marker,
            heading_suffixes=(" (this push)",) if marker == "### Resolution metrics" else (),
        )
        if idx >= 0:
            prefix = markdown[:idx].rstrip()
            suffix = markdown[idx:]
            return f"{prefix}\n\n{block}\n\n{suffix}"
    for marker in ("### Files needing attention", "### This generation"):
        idx = _find_splice_marker(markdown, marker)
        if idx >= 0:
            prefix = markdown[:idx].rstrip()
            suffix = markdown[idx:]
            return f"{prefix}\n\n{block}\n\n{suffix}"
    footer_idx = _find_review_footer_insert_index(markdown)
    if footer_idx >= 0:
        return f"{markdown[:footer_idx].rstrip()}\n\n{block}\n\n{markdown[footer_idx:].lstrip()}"
    return f"{markdown.rstrip()}\n\n{block}"


def _strip_rollup_metadata_footer(markdown: str) -> str:
    marker = "\n---\n*"
    idx = markdown.rfind(marker)
    if idx < 0:
        return markdown
    tail = markdown[idx:]
    if "Revision:" in tail and tail.rstrip().endswith("*"):
        return markdown[:idx].rstrip()
    return markdown


def append_review_metadata_footer(markdown: str, ctx: PublishFormatContext) -> str:
    """Replace legacy review metadata with rollup-aware footer (issue comment only)."""
    markdown = _strip_rollup_metadata_footer(markdown)
    rollup = ctx.pr_resolution_rollup if isinstance(ctx.pr_resolution_rollup, dict) else {}
    review_count = int(rollup.get("review_count") or 0) or None
    head_sha = ctx.head_sha or ""
    short_sha = head_sha[:7] if len(head_sha) >= 7 else (head_sha or "unknown")
    parts = []
    if review_count is not None:
        parts.append(f"Reviews on this PR: {review_count}")
    parts.append(f"Revision: {ctx.revision_number}")
    parts.append(f"Head: {short_sha}")
    footer = f"---\n*{' · '.join(parts)}*"
    summary_idx = markdown.find("<summary>Review metadata</summary>")
    if summary_idx >= 0:
        start = markdown.rfind("<details>", 0, summary_idx)
        if start >= 0:
            end = markdown.find("</details>", summary_idx)
            if end >= 0:
                end += len("</details>")
                return markdown[:start].rstrip() + f"\n\n{footer}\n"
    if footer in markdown:
        return markdown
    return f"{markdown.rstrip()}\n\n{footer}"


def apply_rollup_to_publish_surfaces(
    check_summary: str,
    issue_comment: str,
    ctx: PublishFormatContext,
) -> tuple[str, str]:
    """Apply PR summary block + check one-liners after rollup manifest is available."""
    if not isinstance(ctx.pr_resolution_rollup, dict):
        return check_summary, issue_comment
    issue_comment = splice_deterministic_pr_summary_block(issue_comment, ctx)
    issue_comment = append_review_metadata_footer(issue_comment, ctx)
    one_liners = "\n".join(
        [
            format_pr_rollup_check_one_liner(ctx.pr_resolution_rollup),
            format_push_delta_check_one_liner(ctx),
            "",
        ]
    )
    conf_idx = check_summary.find("**Confidence:**")
    lifetime_line = format_pr_rollup_check_one_liner(ctx.pr_resolution_rollup)
    if conf_idx >= 0:
        after_conf = check_summary.find("\n\n", conf_idx)
        if after_conf >= 0:
            tail = check_summary[after_conf + 2 :]
            if lifetime_line not in tail:
                check_summary = check_summary[: after_conf + 2] + one_liners + tail
        elif lifetime_line not in check_summary:
            check_summary = f"{check_summary}\n\n{one_liners}"
    elif lifetime_line not in check_summary:
        check_summary = f"{check_summary}\n\n{one_liners}"
    return check_summary, issue_comment


_SECTION_END_MARKERS = ("\n### ", "\n<details>", "\n---\n")


def _replace_markdown_section(
    markdown: str,
    start_marker: str,
    new_block: str,
) -> str:
    if start_marker == _PR_SUMMARY_HEADING:
        return _replace_pr_summary_section(markdown, new_block)
    start = markdown.find(start_marker)
    if start < 0:
        return markdown
    end = start + len(start_marker)
    tail = markdown[end:]
    end_offset = len(tail)
    for marker in _SECTION_END_MARKERS:
        idx = tail.find(marker)
        if idx >= 0:
            end_offset = min(end_offset, idx)
    replacement = new_block.rstrip()
    if replacement:
        replacement = f"{replacement}\n"
    return markdown[:start] + replacement + tail[end_offset:].lstrip("\n")


def _replace_details_section(
    markdown: str,
    summary_label: str,
    new_lines: list[str],
) -> str:
    marker = f"<summary>{summary_label}</summary>"
    idx = markdown.find(marker)
    if idx < 0:
        return markdown
    details_start = markdown.rfind("<details>", 0, idx)
    if details_start < 0:
        return markdown
    details_end = markdown.find("</details>", idx)
    if details_end < 0:
        return markdown
    details_end += len("</details>")
    return markdown[:details_start] + "\n".join(new_lines) + markdown[details_end:]


def _remove_details_section(markdown: str, summary_label: str) -> str:
    marker = f"<summary>{summary_label}</summary>"
    idx = markdown.find(marker)
    if idx < 0:
        return markdown
    details_start = markdown.rfind("<details>", 0, idx)
    if details_start < 0:
        return markdown
    details_end = markdown.find("</details>", idx)
    if details_end < 0:
        return markdown
    details_end += len("</details>")
    return (markdown[:details_start] + markdown[details_end:]).strip()


def _patch_issue_narrative_paragraph(issue_comment: str, ctx: PublishFormatContext) -> str:
    if not issue_comment.startswith("## Revy code review"):
        return issue_comment
    narrative = _review_narrative_paragraph(ctx)
    rest = issue_comment[len("## Revy code review") :].lstrip("\n")
    end_offset = len(rest)
    for marker in (
        "\n\n**Merge recommendation:**",
        "\n\n**Confidence score:**",
        "\n\n### ",
        "\n\n<details>",
        "\n\n---",
    ):
        idx = rest.find(marker)
        if idx >= 0:
            end_offset = min(end_offset, idx)
    tail = rest[end_offset:].lstrip("\n")
    return f"## Revy code review\n\n{narrative}\n\n{tail}" if tail else f"## Revy code review\n\n{narrative}"


def _refresh_issue_pr_verdict_sections(issue_comment: str, ctx: PublishFormatContext) -> str:
    """Patch PR-wide verdict blocks after collapse without re-running Moonshot."""
    verdict = verdict_groups(ctx)
    confidence = compute_publish_confidence(ctx)
    updated = issue_comment
    merge_line = f"**Merge recommendation:** {_merge_recommendation(verdict)}"
    if "**Merge recommendation:**" in updated:
        updated = re.sub(
            r"\*\*Merge recommendation:\*\* [^\n]+",
            lambda _: merge_line,
            updated,
            count=1,
        )
    confidence_line = f"**Confidence score:** {confidence}/5"
    if "**Confidence score:**" in updated:
        updated = re.sub(
            r"\*\*Confidence score:\*\* \d+/5",
            lambda _: confidence_line,
            updated,
            count=1,
        )
    attention = _files_needing_attention(verdict)
    if attention:
        files_block = "### Files needing attention\n\n" + "\n".join(
            f"- `{path}`" for path in attention
        )
    elif not _active_groups(verdict):
        files_block = "No files require special attention on this revision."
    else:
        files_block = ""
    if "### Files needing attention" in updated:
        updated = _replace_markdown_section(updated, "### Files needing attention", files_block)
    security_lines = _security_details_lines(verdict)
    if "<summary>Security review</summary>" in updated:
        if security_lines:
            updated = _replace_details_section(updated, "Security review", security_lines)
        else:
            updated = _remove_details_section(updated, "Security review")
    important_lines = _important_files_details_lines(verdict)
    if "<summary>Important files changed</summary>" in updated:
        if important_lines:
            updated = _replace_details_section(updated, "Important files changed", important_lines)
        else:
            updated = _remove_details_section(updated, "Important files changed")
    return _patch_issue_narrative_paragraph(updated, ctx)


def apply_publish_summary_thread_collapse(
    check_summary: str,
    issue_comment: str,
    ctx: PublishFormatContext,
    *,
    publishable_fingerprints: set[str],
    collapsed_fingerprints: set[str],
) -> PublishFormatResult:
    """Refresh publish surfaces after new inline thread collapses this flush."""
    if not collapsed_fingerprints:
        return PublishFormatResult(
            check_summary=check_summary,
            issue_comment=issue_comment,
            confidence=compute_publish_confidence(ctx),
            summary_json=_build_summary_json(ctx),
        )
    pr_active = ctx.pr_active_groups or []
    generation_fingerprints = {group.fingerprint for group in ctx.groups}
    filtered = filter_pr_active_groups_for_summary(
        pr_active,
        publishable_fingerprints=publishable_fingerprints,
        collapsed_fingerprints=collapsed_fingerprints,
        generation_fingerprints=generation_fingerprints,
        ever_inlined_fingerprints=(
            set(ctx.ever_inlined_fingerprints)
            if ctx.ever_inlined_fingerprints is not None
            else None
        ),
    )
    filtered_ctx = replace(ctx, pr_active_groups=filtered)
    confidence = compute_publish_confidence(filtered_ctx)
    new_check = build_check_run_summary(filtered_ctx)
    new_issue = splice_deterministic_findings_tables(issue_comment, filtered_ctx)
    if new_issue == issue_comment:
        new_issue = build_pr_review_comment_fallback(filtered_ctx)
    else:
        new_issue = _refresh_issue_pr_verdict_sections(new_issue, filtered_ctx)
    return PublishFormatResult(
        check_summary=new_check,
        issue_comment=new_issue,
        confidence=confidence,
        summary_json=_build_summary_json(filtered_ctx),
    )


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
    ]
    if isinstance(ctx.pr_resolution_rollup, dict):
        lines.extend(
            [
                format_pr_rollup_check_one_liner(ctx.pr_resolution_rollup),
                format_push_delta_check_one_liner(ctx),
                "",
            ]
        )
    lines.append(
        format_summary_comment(
            generation_groups=ctx.groups,
            pr_active_groups=verdict,
        )
    )
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
    return format_resolution_metrics_block(
        ctx.resolution_metrics_manifest,
        display_still_open_prior=display_still_open_prior_count(ctx),
    )


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

    if isinstance(ctx.pr_resolution_rollup, dict):
        lines.extend(["", format_pr_resolution_rollup_block(ctx.pr_resolution_rollup)])

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

    body = "\n".join(lines)
    body = append_review_metadata_footer(body, ctx)

    footer = _index_footer(ctx)
    if footer:
        body = f"{body}\n\n{footer}"

    return body


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


def _findings_tables_markdown(ctx: PublishFormatContext) -> str:
    return format_summary_comment(
        generation_groups=ctx.groups,
        pr_active_groups=verdict_groups(ctx),
    )


_FINDINGS_TABLES_START_RE = re.compile(r"### This generation(?: findings)?\b", re.IGNORECASE)
_FINDINGS_TABLES_STILL_OPEN_RE = re.compile(
    r"### Still open on PR(?: findings)?\b",
    re.IGNORECASE,
)


def splice_deterministic_findings_tables(markdown: str, ctx: PublishFormatContext) -> str:
    """Replace Moonshot findings tables with DB-backed FR-Q7 blocks (PSA-D1)."""
    start_match = _FINDINGS_TABLES_START_RE.search(markdown)
    if start_match is None:
        return markdown
    start = start_match.start()
    still_match = _FINDINGS_TABLES_STILL_OPEN_RE.search(markdown, start)
    if still_match is None:
        return markdown
    still_start = still_match.start()
    tail = markdown[still_start:]
    end_offset = len(tail)
    for marker in ("\n### ", "\n<details>", "\n---\n"):
        idx = tail.find(marker, 1)
        if idx > 0:
            end_offset = min(end_offset, idx)
    end = still_start + end_offset
    return markdown[:start] + _findings_tables_markdown(ctx) + markdown[end:]


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
    rollup = ctx.pr_resolution_rollup if isinstance(ctx.pr_resolution_rollup, dict) else {}
    review_count = int(rollup.get("review_count") or 0)
    raised_count = int(rollup.get("raised_count") or 0)
    needs_pr_summary = review_count > 1 or raised_count > 0
    has_pr_summary = "### PR summary" in normalized
    if needs_pr_summary and not has_pr_summary:
        return False
    if "### Findings" in normalized and not has_generation_block:
        return False
    return (
        has_generation_block and has_pr_block and has_table and has_merge_signal and has_rationale
    )


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
    prompt = (
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
        f"Generation active count: {len(generation_active)}; PR active count: {len(pr_active)}\n"
        f"Revision note: when revision_number is 1, PR active count equals generation count "
        f"(no prior push); both tables must list the same rows."
    )
    if isinstance(ctx.pr_resolution_rollup, dict):
        prompt += (
            "\nPR lifetime rollup JSON (deterministic formatter owns the full ### PR summary block; "
            "Moonshot must not emit scan tables or <details> for lifetime — heading stub at most):\n"
            f"{json.dumps(ctx.pr_resolution_rollup, ensure_ascii=False)}\n"
            "Do not omit ### PR summary (lifetime) when review_count > 1 or raised_count > 0."
        )
    return prompt


async def build_pr_review_comment_with_model(
    ctx: PublishFormatContext,
) -> tuple[str, str | None, str | None]:
    """Returns markdown and optional publish model provider/id when the reviewer LLM runs."""
    fallback = build_pr_review_comment_fallback(ctx)
    if not settings.reviewer_llm_enabled():
        return fallback, None, None

    prompt = _build_issue_comment_user_prompt(ctx)
    provider = settings.effective_reviewer_provider
    if provider not in {"moonshot", "rtu"}:
        return fallback, None, None
    model_id = settings.revy_reviewer_model_for_profile("standard")
    api_url = None
    api_key = None
    if provider == "rtu":
        api_url = settings.rtu_chat_completions_url
        api_key = settings.effective_rtu_api_key
    recorder = None
    if ctx.pipeline_run_id is not None and ctx.review_run_id is not None:
        recorder = LlmAttemptStartContext(
            pipeline_run_id=ctx.pipeline_run_id,
            review_run_id=ctx.review_run_id,
            index_job_id=None,
            step_type=LlmCallStepType.publish,
            operation_name=LlmCallOperationName.chat,
            attempt_no=0,
            provider=provider,
            request_model=model_id,
        )

    def _publish_model_fields() -> tuple[str | None, str | None]:
        if recorder is None:
            return None, None
        return recorder.provider, model_id

    try:
        async with httpx.AsyncClient(
            timeout=float(settings.revy_revision_timeout_standard_seconds)
        ) as client:
            raw = await moonshot_review.complete_issue_comment_markdown(
                client,
                profile="standard",
                user_prompt=prompt,
                model_id=model_id,
                recorder=recorder,
                api_url=api_url,
                api_key=api_key,
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
            return fallback, None, None
        if not _issue_comment_meets_product_bar(text, ctx):
            logger.warning(
                "github_publish_formatter_llm_thin_markdown",
                extra={
                    "pull_request_id": str(ctx.pull_request_id),
                    "raw_prefix": text.strip()[:200],
                },
            )
            return fallback, None, None
        text = splice_deterministic_findings_tables(text, ctx)
        text = splice_deterministic_pr_summary_block(text, ctx)
        text = append_review_metadata_footer(text, ctx)
        footer = _index_footer(ctx)
        if footer and footer not in text:
            text = f"{text}\n\n{footer}"
        publish_provider, publish_model = _publish_model_fields()
        return _append_resolution_metrics_block(text, ctx), publish_provider, publish_model
    except (httpx.HTTPError, ValueError, OSError, ServiceUnavailableError) as exc:
        logger.warning(
            "github_publish_formatter_llm_failed",
            extra={"pull_request_id": str(ctx.pull_request_id), "error": str(exc)},
        )

    return fallback, None, None


async def build_pr_review_comment(ctx: PublishFormatContext) -> str:
    """Backward-compatible wrapper — returns issue comment markdown only."""
    markdown, _, _ = await build_pr_review_comment_with_model(ctx)
    return markdown


def _build_summary_json(ctx: PublishFormatContext) -> dict:
    verdict = verdict_groups(ctx)
    confidence = compute_publish_confidence(ctx)
    if ctx.resolution_metrics_manifest is not None:
        resolution = resolution_counts_from_manifest(ctx.resolution_metrics_manifest)
        resolution[ResolutionStatus.still_open.value] = display_still_open_prior_count(ctx)
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
        **(
            {"pr_resolution_rollup": ctx.pr_resolution_rollup}
            if isinstance(ctx.pr_resolution_rollup, dict)
            else {}
        ),
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
    issue_comment, publish_provider, publish_model_id = await build_pr_review_comment_with_model(ctx)
    summary_json = _build_summary_json(ctx)
    return PublishFormatResult(
        check_summary=check_summary,
        issue_comment=issue_comment,
        confidence=summary_json["confidence"],
        summary_json=summary_json,
        publish_model_provider=publish_provider,
        publish_model_id=publish_model_id,
    )
