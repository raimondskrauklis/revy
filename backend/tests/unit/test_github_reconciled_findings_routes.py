# backend/tests/unit/test_github_reconciled_findings_routes.py
"""Reconciled findings routes — R5."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.workspaces.installation_review import get_reconciled_findings
from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
)
from app.core.pagination import CursorMeta, CursorParams, CursorResponse
from app.schemas.github_review import ReconciledFindingResponse


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
