# backend/tests/unit/test_workspace_model_policy_routes.py
"""Workspace model policy routes — MODEL_POLICY M2."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.workspaces.model_policy import (
    get_model_catalog,
    get_model_policy,
    patch_model_policy,
)
from app.constants.enums import AppRole, UserStatus
from app.core.auth import CurrentUser
from app.core.exceptions import ForbiddenError
from app.schemas.model_policy import ModelPolicyEntry, ModelPolicyPatch, ModelPolicyResponse


def _admin_user(workspace_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        sub="kc-admin",
        actor_user_id=uuid.uuid4(),
        email="admin@example.com",
        workspace_id=workspace_id,
        role=AppRole.admin,
        status=UserStatus.active,
    )


@pytest.mark.asyncio
async def test_get_model_policy_returns_response():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=object())
    expected = ModelPolicyResponse(overrides={}, effective={})

    with patch(
        "app.api.v1.workspaces.model_policy.get_workspace_model_policy",
        AsyncMock(return_value=expected),
    ):
        response = await get_model_policy(
            workspace_id=workspace_id,
            current_user=_admin_user(workspace_id),
            session=session,
        )

    assert response.data == expected


@pytest.mark.asyncio
async def test_get_model_policy_denies_other_workspace():
    workspace_id = uuid.uuid4()
    session = AsyncMock()

    with pytest.raises(ForbiddenError):
        await get_model_policy(
            workspace_id=workspace_id,
            current_user=_admin_user(uuid.uuid4()),
            session=session,
        )


@pytest.mark.asyncio
async def test_patch_model_policy_commits():
    workspace_id = uuid.uuid4()
    user = _admin_user(workspace_id)
    session = AsyncMock()
    session.get = AsyncMock(return_value=object())
    session.commit = AsyncMock()
    expected = ModelPolicyResponse(overrides={}, effective={})
    body = ModelPolicyPatch(
        judge=ModelPolicyEntry(provider="anthropic", model_id="claude-sonnet-4-20250514"),
    )

    with patch(
        "app.api.v1.workspaces.model_policy.patch_workspace_model_policy",
        AsyncMock(return_value=expected),
    ):
        response = await patch_model_policy(
            workspace_id=workspace_id,
            body=body,
            current_user=user,
            session=session,
        )

    session.commit.assert_awaited_once()
    assert response.data == expected


@pytest.mark.asyncio
async def test_get_model_catalog_returns_roles():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=object())

    with patch(
        "app.api.v1.workspaces.model_policy.build_model_catalog",
        return_value={"judge": []},
    ):
        response = await get_model_catalog(
            workspace_id=workspace_id,
            current_user=_admin_user(workspace_id),
            session=session,
        )

    assert "judge" in response.data.roles
