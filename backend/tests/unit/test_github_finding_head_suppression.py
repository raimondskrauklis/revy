# backend/tests/unit/test_github_finding_head_suppression.py
"""HEAD contradiction suppression — RR-W1 R4."""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    ResolutionMethod,
)
from app.models.github_finding_group import GitHubFindingGroupORM
from app.services.github_finding_head_suppression import (
    HEAD_CONTRADICTION_MATCHERS,
    matches_head_contradiction,
    suppress_head_contradictions,
)


def _group(*, title: str, message: str, file_path: str = "app/example.py") -> GitHubFindingGroupORM:
    return GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint=uuid.uuid4().hex,
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title=title,
        message=message,
        file_path=file_path,
        last_seen_revision_id=uuid.uuid4(),
    )


def test_matches_head_contradiction_matrix_row_missing_or_import():
    group = _group(
        title="Missing sqlalchemy or_ import",
        message="entities.py does not import or_ from sqlalchemy",
        file_path="backend/app/models/entities.py",
    )
    head = "from sqlalchemy import Column, or_\n"
    assert matches_head_contradiction(group, head) == "missing_or_import"


def test_matches_head_contradiction_matrix_row_system_status_bar_props():
    group = _group(
        title="SystemStatusBar missing required props",
        message="SystemStatusBar requires connectionId and compact as required props",
        file_path="frontend/src/components/SystemStatusBar.tsx",
    )
    head = "type Props = { connectionId?: string; compact?: boolean }\n"
    assert matches_head_contradiction(group, head) == "system_status_bar_props"


def test_matches_head_contradiction_system_status_bar_single_optional_prop_no_match():
    group = _group(
        title="SystemStatusBar missing required props",
        message="SystemStatusBar requires connectionId and compact",
        file_path="frontend/src/components/SystemStatusBar.tsx",
    )
    head = "type Props = { connectionId?: string }\n"
    assert matches_head_contradiction(group, head) is None


def test_matches_head_contradiction_matrix_row_kpi_skeleton_count():
    group = _group(
        title="Wrong KPI skeleton count",
        message="Overview renders wrong number of KPI skeletons",
        file_path="frontend/src/features/dashboard/Overview.tsx",
    )
    head = "const OVERVIEW_KPI_COUNT = 4\n"
    assert matches_head_contradiction(group, head) == "kpi_skeleton_count"


def test_matches_head_contradiction_matrix_row_export_label():
    group = _group(
        title="Export label misleading",
        message="Export button label is always wrong",
        file_path="frontend/src/features/export/ExportPanel.tsx",
    )
    head = 'label={selected.length ? "Export Selected" : "Export List"}\n'
    assert matches_head_contradiction(group, head) == "export_label"


def test_matches_head_contradiction_matrix_row_prop_migration():
    group = _group(
        title="Callers missing required props",
        message="Prop migration incomplete on dashboard callers",
        file_path="frontend/src/features/dashboard/DashboardPage.tsx",
    )
    head = "<SystemStatusBar connectionId? compact? />\n"
    assert matches_head_contradiction(group, head) == "prop_migration"


def test_matches_head_contradiction_returns_none_when_claim_still_valid():
    group = _group(
        title="Missing sqlalchemy or_ import",
        message="entities.py does not import or_",
        file_path="backend/app/models/entities.py",
    )
    head = "from sqlalchemy import Column\n"
    assert matches_head_contradiction(group, head) is None


def test_head_contradiction_matchers_cover_rr_v5_rows():
    assert {rule_id for rule_id, _ in HEAD_CONTRADICTION_MATCHERS} == {
        "missing_or_import",
        "system_status_bar_props",
        "kpi_skeleton_count",
        "export_label",
        "prop_migration",
    }


@pytest.mark.asyncio
async def test_suppress_head_contradictions_resolves_contradicted_group():
    revision_id = uuid.uuid4()
    group = _group(
        title="Missing sqlalchemy or_ import",
        message="entities.py does not import or_",
        file_path="backend/app/models/entities.py",
    )
    session = AsyncMock()
    suppressed = await suppress_head_contradictions(
        session,
        groups=[group],
        head_file_snippets={
            "backend/app/models/entities.py": "from sqlalchemy import or_\n",
        },
        current_revision_id=revision_id,
    )
    assert suppressed == 1
    assert group.state == GitHubFindingGroupState.resolved
    assert group.resolution_method == ResolutionMethod.head_contradiction
    assert group.resolved_at_revision_id == revision_id
    assert group.closure_blocked_reason is None
    assert group.resolution_status is None


@pytest.mark.asyncio
async def test_suppress_head_contradictions_clears_stale_closure_blocked_reason():
    revision_id = uuid.uuid4()
    group = _group(
        title="Missing sqlalchemy or_ import",
        message="entities.py does not import or_",
        file_path="backend/app/models/entities.py",
    )
    group.closure_blocked_reason = "compare_failed"
    group.resolution_status = "still_open"
    session = AsyncMock()
    await suppress_head_contradictions(
        session,
        groups=[group],
        head_file_snippets={
            "backend/app/models/entities.py": "from sqlalchemy import or_\n",
        },
        current_revision_id=revision_id,
    )
    assert group.closure_blocked_reason is None
    assert group.resolution_status is None
