# backend/app/services/github_finding_head_suppression.py
"""HEAD contradiction suppression — RR-W1 R4 (RR-DG6).

Matchers are pluggable rules keyed by ``rule_id``. RR-V5 staging fixtures
(operator matrix rows 1, 2, 3, 15, 17) seed the default registry; add new
``HeadContradictionRule`` entries for other repos without changing reconcile hook.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
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

HeadContradictionMatcher = Callable[[GitHubFindingGroupORM, str], bool]


@dataclass(frozen=True, slots=True)
class HeadContradictionRule:
    rule_id: str
    matrix_ref: str
    matcher: HeadContradictionMatcher


def _claim_text(group: GitHubFindingGroupORM) -> str:
    return f"{group.title}\n{group.message}".lower()


def _claim_mentions_sqlalchemy_or_import(group: GitHubFindingGroupORM) -> bool:
    claim = _claim_text(group)
    return ("or_" in claim or "or " in claim) and ("import" in claim or "sqlalchemy" in claim)


def _head_imports_sqlalchemy_or(head_content: str) -> bool:
    lowered = head_content.lower()
    return "or_" in lowered and "sqlalchemy" in lowered


def _claim_mentions_system_status_bar_required_props(group: GitHubFindingGroupORM) -> bool:
    claim = _claim_text(group)
    return "systemstatusbar" in claim and ("required" in claim or "missing" in claim)


def _head_system_status_bar_optional_props(head_content: str) -> bool:
    return "connectionId?" in head_content and "compact?" in head_content


def _claim_mentions_kpi_skeleton(group: GitHubFindingGroupORM) -> bool:
    claim = _claim_text(group)
    return "kpi" in claim or "skeleton" in claim


def _matches_missing_or_import(group: GitHubFindingGroupORM, head_content: str) -> bool:
    return _claim_mentions_sqlalchemy_or_import(group) and _head_imports_sqlalchemy_or(head_content)


def _matches_system_status_bar_props(group: GitHubFindingGroupORM, head_content: str) -> bool:
    return _claim_mentions_system_status_bar_required_props(
        group
    ) and _head_system_status_bar_optional_props(head_content)


def _matches_kpi_skeleton_count(group: GitHubFindingGroupORM, head_content: str) -> bool:
    return _claim_mentions_kpi_skeleton(group) and "OVERVIEW_KPI_COUNT = 4" in head_content


def _matches_export_label(group: GitHubFindingGroupORM, head_content: str) -> bool:
    claim = _claim_text(group)
    return "export" in claim and "Export List" in head_content and "Export Selected" in head_content


def _matches_prop_migration(group: GitHubFindingGroupORM, head_content: str) -> bool:
    claim = _claim_text(group)
    return ("prop" in claim or "caller" in claim) and _head_system_status_bar_optional_props(
        head_content
    )


HEAD_CONTRADICTION_RULES: tuple[HeadContradictionRule, ...] = (
    HeadContradictionRule(
        rule_id="missing_or_import",
        matrix_ref="RR-V5 row 1",
        matcher=_matches_missing_or_import,
    ),
    HeadContradictionRule(
        rule_id="system_status_bar_props",
        matrix_ref="RR-V5 row 2",
        matcher=_matches_system_status_bar_props,
    ),
    HeadContradictionRule(
        rule_id="kpi_skeleton_count",
        matrix_ref="RR-V5 row 3",
        matcher=_matches_kpi_skeleton_count,
    ),
    HeadContradictionRule(
        rule_id="export_label",
        matrix_ref="RR-V5 row 15",
        matcher=_matches_export_label,
    ),
    HeadContradictionRule(
        rule_id="prop_migration",
        matrix_ref="RR-V5 row 17",
        matcher=_matches_prop_migration,
    ),
)

HEAD_CONTRADICTION_MATCHERS: tuple[tuple[str, HeadContradictionMatcher], ...] = tuple(
    (rule.rule_id, rule.matcher) for rule in HEAD_CONTRADICTION_RULES
)


def matches_head_contradiction(
    group: GitHubFindingGroupORM,
    head_content: str,
) -> str | None:
    for rule in HEAD_CONTRADICTION_RULES:
        if rule.matcher(group, head_content):
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
