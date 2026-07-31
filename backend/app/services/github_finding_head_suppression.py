# backend/app/services/github_finding_head_suppression.py
"""HEAD contradiction suppression — RR-W1 R4 (RR-DG6).

Matchers are pluggable ``HeadContradictionRule`` entries keyed by ``rule_id``.
Each rule pairs a compiled claim regex (finding text) with a head predicate
(file content at ``head_sha``). RR-V5 matrix rows seed the default registry.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from re import Pattern
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import GitHubFindingGroupState, ResolutionMethod
from app.core.exceptions import NotFoundError, RateLimitedError, ServiceUnavailableError
from app.core.logging import get_logger
from app.integrations.github_api import fetch_repository_file_at_sha
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM
from app.models.github_review_run import GitHubReviewRunORM

logger = get_logger(__name__)

HeadContentPredicate = Callable[[str], bool]

_CLAIM_SQLALCHEMY_OR_MISSING_RE = re.compile(
    r"(?:\bor_\b[^\n]{0,120}\b(?:sqlalchemy|import)\b|\b(?:sqlalchemy|import)\b[^\n]{0,120}\bor_\b)",
    re.IGNORECASE,
)
_HEAD_SQLALCHEMY_OR_IMPORT_RE = re.compile(
    r"(?:from\s+sqlalchemy\b[^\n;]*\bor_\b|\bimport\s+sqlalchemy\b[^\n;]*\bor_\b)",
    re.IGNORECASE,
)

_CLAIM_SYSTEM_STATUS_BAR_REQUIRED_RE = re.compile(
    r"\bsystem\s*status\s*bar\b",
    re.IGNORECASE,
)
_CLAIM_REQUIRED_OR_MISSING_RE = re.compile(r"\b(?:required|missing)\b", re.IGNORECASE)
_HEAD_TS_OPTIONAL_PROPS_RE = re.compile(
    r"connectionId\s*\?\s*:[^}]*compact\s*\?\s*:",
    re.IGNORECASE | re.DOTALL,
)
_HEAD_JSX_OPTIONAL_PROPS_RE = re.compile(
    r"connectionId\s*\?[^\n/>]*compact\s*\?",
    re.IGNORECASE,
)

_CLAIM_KPI_SKELETON_RE = re.compile(r"\b(?:kpi|skeleton)\b", re.IGNORECASE)
_HEAD_OVERVIEW_KPI_COUNT_FOUR_RE = re.compile(r"\bOVERVIEW_KPI_COUNT\s*=\s*4\b")

_CLAIM_EXPORT_LABEL_RE = re.compile(r"\bexport\b", re.IGNORECASE)
_HEAD_EXPORT_LIST_RE = re.compile(r"""['"]Export List['"]""")
_HEAD_EXPORT_SELECTED_RE = re.compile(r"""['"]Export Selected['"]""")

_CLAIM_PROP_MIGRATION_RE = re.compile(r"\b(?:prop|caller)s?\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class HeadContradictionRule:
    rule_id: str
    matrix_ref: str
    claim_predicate: Callable[[GitHubFindingGroupORM], bool]
    head_predicate: HeadContentPredicate


def _claim_text(group: GitHubFindingGroupORM) -> str:
    return f"{group.title}\n{group.message}"


def _claim_matches(pattern: Pattern[str], group: GitHubFindingGroupORM) -> bool:
    return pattern.search(_claim_text(group)) is not None


def _head_imports_sqlalchemy_or(head_content: str) -> bool:
    return _HEAD_SQLALCHEMY_OR_IMPORT_RE.search(head_content) is not None


def _head_system_status_bar_optional_props(head_content: str) -> bool:
    return (
        _HEAD_TS_OPTIONAL_PROPS_RE.search(head_content) is not None
        or _HEAD_JSX_OPTIONAL_PROPS_RE.search(head_content) is not None
    )


def _head_has_overview_kpi_count_four(head_content: str) -> bool:
    return _HEAD_OVERVIEW_KPI_COUNT_FOUR_RE.search(head_content) is not None


def _head_has_conditional_export_labels(head_content: str) -> bool:
    return (
        _HEAD_EXPORT_LIST_RE.search(head_content) is not None
        and _HEAD_EXPORT_SELECTED_RE.search(head_content) is not None
    )


def _claim_system_status_bar_required(group: GitHubFindingGroupORM) -> bool:
    claim = _claim_text(group)
    return (
        _CLAIM_SYSTEM_STATUS_BAR_REQUIRED_RE.search(claim) is not None
        and _CLAIM_REQUIRED_OR_MISSING_RE.search(claim) is not None
    )


HEAD_CONTRADICTION_RULES: tuple[HeadContradictionRule, ...] = (
    HeadContradictionRule(
        rule_id="missing_or_import",
        matrix_ref="RR-V5 row 1",
        claim_predicate=lambda group: _claim_matches(_CLAIM_SQLALCHEMY_OR_MISSING_RE, group),
        head_predicate=_head_imports_sqlalchemy_or,
    ),
    HeadContradictionRule(
        rule_id="system_status_bar_props",
        matrix_ref="RR-V5 row 2",
        claim_predicate=_claim_system_status_bar_required,
        head_predicate=_head_system_status_bar_optional_props,
    ),
    HeadContradictionRule(
        rule_id="kpi_skeleton_count",
        matrix_ref="RR-V5 row 3",
        claim_predicate=lambda group: _claim_matches(_CLAIM_KPI_SKELETON_RE, group),
        head_predicate=_head_has_overview_kpi_count_four,
    ),
    HeadContradictionRule(
        rule_id="export_label",
        matrix_ref="RR-V5 row 15",
        claim_predicate=lambda group: _claim_matches(_CLAIM_EXPORT_LABEL_RE, group),
        head_predicate=_head_has_conditional_export_labels,
    ),
    HeadContradictionRule(
        rule_id="prop_migration",
        matrix_ref="RR-V5 row 17",
        claim_predicate=lambda group: _claim_matches(_CLAIM_PROP_MIGRATION_RE, group),
        head_predicate=_head_system_status_bar_optional_props,
    ),
)


def matches_head_contradiction(
    group: GitHubFindingGroupORM,
    head_content: str,
) -> str | None:
    for rule in HEAD_CONTRADICTION_RULES:
        if rule.claim_predicate(group) and rule.head_predicate(head_content):
            return rule.rule_id
    return None


async def _load_head_file_snippets(
    session: AsyncSession,
    *,
    pull_request: GitHubPullRequestORM,
    head_sha: str,
    file_paths: frozenset[str],
    client: httpx.AsyncClient | None = None,
) -> dict[str, str]:
    if not file_paths or not head_sha:
        return {}

    repository = await session.get(GitHubRepositoryORM, pull_request.repository_id)
    installation = await session.get(GitHubInstallationORM, pull_request.installation_id)
    if repository is None or installation is None or "/" not in repository.full_name:
        return {}

    owner, repo_name = repository.full_name.split("/", 1)
    github_installation_id = installation.github_installation_id

    async def _fetch(http_client: httpx.AsyncClient) -> dict[str, str]:
        snippets: dict[str, str] = {}
        for file_path in sorted(file_paths):
            try:
                snippets[file_path] = await fetch_repository_file_at_sha(
                    http_client,
                    github_installation_id=github_installation_id,
                    owner=owner,
                    repo=repo_name,
                    path=file_path,
                    ref=head_sha,
                )
            except (
                httpx.HTTPError,
                OSError,
                NotFoundError,
                RateLimitedError,
                ServiceUnavailableError,
            ):
                continue
        return snippets

    if client is not None:
        return await _fetch(client)

    async with httpx.AsyncClient(timeout=60.0) as http_client:
        return await _fetch(http_client)


async def suppress_head_contradictions(
    session: AsyncSession,
    *,
    groups: list[GitHubFindingGroupORM],
    head_file_snippets: dict[str, str],
    current_revision_id: UUID,
) -> int:
    """Mark active groups contradicted by HEAD file text as resolved."""
    suppressed = 0
    for group in groups:
        if group.state != GitHubFindingGroupState.active:
            continue
        file_path = group.file_path
        if not file_path:
            continue
        head_content = head_file_snippets.get(file_path)
        if not head_content:
            continue
        rule_id = matches_head_contradiction(group, head_content)
        if rule_id is None:
            continue
        group.state = GitHubFindingGroupState.resolved
        group.resolution_method = ResolutionMethod.head_contradiction
        group.resolved_at_revision_id = current_revision_id
        group.closure_blocked_reason = None
        group.resolution_status = None
        suppressed += 1
        logger.info(
            "finding_suppressed_head_contradiction",
            extra={
                "fingerprint": group.fingerprint,
                "file_path": file_path,
                "rule_id": rule_id,
            },
        )
    if suppressed:
        await session.flush()
    return suppressed


async def suppress_head_contradictions_for_review_run(
    session: AsyncSession,
    *,
    review_run_id: UUID,
    client: httpx.AsyncClient | None = None,
) -> int:
    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None:
        return 0
    revision = await session.get(GitHubPullRequestRevisionORM, run.revision_id)
    if revision is None:
        return 0
    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    if pull_request is None:
        return 0

    groups = list(
        await session.scalars(
            select(GitHubFindingGroupORM).where(
                GitHubFindingGroupORM.pull_request_id == pull_request.id,
                GitHubFindingGroupORM.state == GitHubFindingGroupState.active,
            )
        )
    )
    if not groups:
        return 0

    file_paths = frozenset(group.file_path for group in groups if group.file_path)
    head_file_snippets = await _load_head_file_snippets(
        session,
        pull_request=pull_request,
        head_sha=revision.head_sha,
        file_paths=file_paths,
        client=client,
    )
    return await suppress_head_contradictions(
        session,
        groups=groups,
        head_file_snippets=head_file_snippets,
        current_revision_id=revision.id,
    )
