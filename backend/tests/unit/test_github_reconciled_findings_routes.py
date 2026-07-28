# backend/tests/unit/test_github_reconciled_findings_routes.py
"""Reconciled findings routes — R5."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.workspaces.installation_review import (
    get_reconciled_findings,
    post_dismiss_finding_group,
)
from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    ResolutionMethod,
    ResolutionStatus,
)
from app.core.pagination import CursorMeta, CursorParams, CursorResponse
from app.models.github_finding_group import GitHubFindingGroupORM
from app.schemas.github_review import DismissFindingGroupRequest, ReconciledFindingResponse


@pytest.mark.asyncio
async def test_get_reconciled_findings_returns_page():
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    group_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    now = datetime.now(UTC)

    item = ReconciledFindingResponse(
        id=group_id,
        pull_request_id=pull_request_id,
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQLi",
        message="Unsanitized",
        file_path="app/db.py",
        last_seen_revision_id=revision_id,
        resolution_status=ResolutionStatus.addressed,
        resolution_method=ResolutionMethod.absent_and_addressed,
        resolved_at_revision_id=revision_id,
        closure_blocked_reason=None,
        created_at=now,
        updated_at=now,
    )
    page = CursorResponse(
        items=[item],
        cursor=CursorMeta(next_cursor=None, has_next=False),
    )

    session = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id

    with patch("app.api.v1.workspaces.installation_review.require_permission"):
        with patch("app.api.v1.workspaces.installation_review.require_same_workspace"):
            with patch(
                "app.api.v1.workspaces.installation_review.list_reconciled_finding_groups",
                AsyncMock(return_value=page),
            ):
                response = await get_reconciled_findings(
                    workspace_id=workspace_id,
                    repository_id=repository_id,
                    pull_request_id=pull_request_id,
                    current_user=current_user,
                    session=session,
                    params=CursorParams(),
                )

    assert len(response.data.items) == 1
    assert response.data.items[0].title == "SQLi"
    assert response.data.items[0].resolution_method == ResolutionMethod.absent_and_addressed


@pytest.mark.asyncio
async def test_post_dismiss_finding_group_returns_resolved_group():
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    group_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(UTC)

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp",
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Lint",
        message="Fix style",
        file_path="app/a.py",
        last_seen_revision_id=revision_id,
        resolution_method=ResolutionMethod.human_dismissed,
        resolved_at_revision_id=revision_id,
        created_at=now,
        updated_at=now,
    )
    group.id = group_id

    session = AsyncMock()
    session.commit = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id
    current_user.user_id = user_id

    with patch("app.api.v1.workspaces.installation_review.require_permission"):
        with patch("app.api.v1.workspaces.installation_review.require_same_workspace"):
            with patch(
                "app.api.v1.workspaces.installation_review.dismiss_finding_group",
                AsyncMock(return_value=group),
            ) as dismiss_mock:
                with patch(
                    "app.api.v1.workspaces.installation_review.record_audit",
                    AsyncMock(),
                ) as audit_mock:
                    response = await post_dismiss_finding_group(
                        workspace_id=workspace_id,
                        repository_id=repository_id,
                        pull_request_id=pull_request_id,
                        group_id=group_id,
                        body=DismissFindingGroupRequest(reason="false positive"),
                        current_user=current_user,
                        session=session,
                    )

    dismiss_mock.assert_awaited_once()
    audit_mock.assert_awaited_once()
    session.commit.assert_awaited_once()
    assert response.data.resolution_method == ResolutionMethod.human_dismissed


def test_resolution_parity_api_and_formatter_counts():
    now = datetime.now(UTC)
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="fp",
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/a.py",
        last_seen_revision_id=revision_id,
        resolution_method=ResolutionMethod.absent_and_addressed,
        resolved_at_revision_id=revision_id,
        created_at=now,
        updated_at=now,
    )
    group.id = uuid.uuid4()

    from app.services.github_publish_formatter import count_resolution_status

    counts = count_resolution_status([group])
    api_item = ReconciledFindingResponse.model_validate(group)

    assert counts[ResolutionStatus.addressed.value] == 1
    assert api_item.resolution_method == ResolutionMethod.absent_and_addressed
    assert api_item.state == GitHubFindingGroupState.resolved
