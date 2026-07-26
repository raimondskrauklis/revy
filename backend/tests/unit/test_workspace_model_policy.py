# backend/tests/unit/test_workspace_model_policy.py
"""Workspace model policy service — MODEL_POLICY M2."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.constants.model_policy import ModelRole
from app.core.exceptions import ValidationError
from app.schemas.model_policy import ModelPolicyEntry, ModelPolicyPatch
from app.services.workspace_model_policy import patch_workspace_model_policy


@pytest.mark.asyncio
async def test_patch_rejects_arbitrary_bedrock_region():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()
    body = ModelPolicyPatch(
        judge=ModelPolicyEntry(
            provider="bedrock",
            model_id="anthropic.claude-sonnet-4-20250514-v1:0",
            region="us-east-1",
        ),
    )

    with (
        patch(
            "app.services.workspace_model_policy.is_valid_catalog_entry",
            return_value=True,
        ),
        patch(
            "app.services.workspace_model_policy.catalog_region_for_provider",
            return_value="eu-central-1",
        ),
        pytest.raises(ValidationError) as exc_info,
    ):
        await patch_workspace_model_policy(
            session,
            workspace_id=workspace_id,
            body=body,
            actor_user_id=uuid.uuid4(),
        )

    assert exc_info.value.field == "judge"


@pytest.mark.asyncio
async def test_patch_stores_platform_bedrock_region_when_client_omits_region():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()
    body = ModelPolicyPatch(
        judge=ModelPolicyEntry(
            provider="bedrock",
            model_id="anthropic.claude-sonnet-4-20250514-v1:0",
            region=None,
        ),
    )

    with (
        patch(
            "app.services.workspace_model_policy.is_valid_catalog_entry",
            return_value=True,
        ),
        patch(
            "app.services.workspace_model_policy.catalog_region_for_provider",
            return_value="eu-central-1",
        ),
        patch(
            "app.services.workspace_model_policy.get_workspace_model_policy",
            AsyncMock(return_value=None),
        ),
        patch("app.services.workspace_model_policy.record_audit", AsyncMock()),
    ):
        await patch_workspace_model_policy(
            session,
            workspace_id=workspace_id,
            body=body,
            actor_user_id=uuid.uuid4(),
        )

    added = session.add.call_args[0][0]
    assert added.region == "eu-central-1"
    assert added.role == ModelRole.judge.value


@pytest.mark.asyncio
async def test_patch_rejects_region_for_non_bedrock_provider():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    body = ModelPolicyPatch(
        judge=ModelPolicyEntry(
            provider="anthropic",
            model_id="claude-sonnet-5",
            region="eu-central-1",
        ),
    )

    with (
        patch(
            "app.services.workspace_model_policy.is_valid_catalog_entry",
            return_value=True,
        ),
        pytest.raises(ValidationError) as exc_info,
    ):
        await patch_workspace_model_policy(
            session,
            workspace_id=workspace_id,
            body=body,
            actor_user_id=uuid.uuid4(),
        )

    assert exc_info.value.field == "judge"
