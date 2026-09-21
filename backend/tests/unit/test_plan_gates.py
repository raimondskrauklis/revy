# backend/tests/unit/test_plan_gates.py
"""Plan feature gating — installations.create gate removed."""
import uuid
from unittest.mock import AsyncMock

import pytest

from app.constants.enums import WorkspaceStatus
from app.core.exceptions import NotFoundError
from app.core.plan_gates import (
    PLAN_FEATURES,
    require_plan_feature,
    workspace_has_feature,
)
from app.models.workspaces import WorkspaceORM


def _workspace(*, plan: str | None) -> WorkspaceORM:
    workspace = WorkspaceORM(
        slug="acme",
        name="Acme Corp",
        status=WorkspaceStatus.active,
        plan=plan,
    )
    workspace.id = uuid.uuid4()
    return workspace


def test_plan_features_is_empty():
    assert PLAN_FEATURES == {}


def test_workspace_has_feature_free_allowed():
    """Free-plan workspaces can install when no plan gate exists."""
    workspace = _workspace(plan=None)
    assert workspace_has_feature(workspace, "installations.create") is True


def test_workspace_has_feature_pro_allowed():
    workspace = _workspace(plan="pro")
    assert workspace_has_feature(workspace, "installations.create") is True


@pytest.mark.asyncio
async def test_require_plan_feature_allows_free_plan():
    """require_plan_feature is a no-op when PLAN_FEATURES is empty."""
    workspace_id = uuid.uuid4()
    workspace = _workspace(plan=None)
    workspace.id = workspace_id
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    dependency = require_plan_feature("installations.create")

    # Should not raise — empty PLAN_FEATURES means all features allowed
    await dependency(workspace_id=workspace_id, session=session)


@pytest.mark.asyncio
async def test_require_plan_feature_allows_pro_plan():
    workspace_id = uuid.uuid4()
    workspace = _workspace(plan="pro")
    workspace.id = workspace_id
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    dependency = require_plan_feature("installations.create")

    await dependency(workspace_id=workspace_id, session=session)


@pytest.mark.asyncio
async def test_require_plan_feature_workspace_not_found():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    dependency = require_plan_feature("installations.create")

    with pytest.raises(NotFoundError):
        await dependency(workspace_id=workspace_id, session=session)