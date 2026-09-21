# backend/tests/unit/test_me_credit_fields.py
"""MeResponse includes credit fields completed_review_runs and review_run_limit."""
from __future__ import annotations

import uuid

import pytest

from app.constants.enums import AppRole, UserStatus
from app.models.workspaces import WorkspaceORM
from app.schemas.me import MeResponse


def _workspace(*, completed: int, limit: int | None) -> WorkspaceORM:
    workspace = WorkspaceORM(
        slug="test-ws",
        name="Test Workspace",
        review_run_limit=limit,
    )
    workspace.id = uuid.uuid4()
    workspace.completed_review_runs = completed
    return workspace


@pytest.mark.asyncio
async def test_me_response_includes_credit_fields():
    """MeResponse can be constructed with credit fields."""
    response = MeResponse(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        status=UserStatus.active,
        platform_role=None,
        workspace_id=uuid.uuid4(),
        role=AppRole.admin,
        locale="en",
        timezone="UTC",
        memberships=[],
        workspace_plan="free",
        completed_review_runs=5,
        review_run_limit=25,
    )

    assert response.completed_review_runs == 5
    assert response.review_run_limit == 25


@pytest.mark.asyncio
async def test_me_response_defaults_for_no_workspace():
    """MeResponse defaults for users without a workspace."""
    response = MeResponse(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        status=UserStatus.pending_profile,
        platform_role=None,
        workspace_id=None,
        role=None,
        locale="en",
        timezone="UTC",
        memberships=[],
    )

    assert response.completed_review_runs == 0
    assert response.review_run_limit is None


@pytest.mark.asyncio
async def test_me_response_pro_null_limit():
    """Pro workspace has review_run_limit = None."""
    response = MeResponse(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        status=UserStatus.active,
        platform_role=None,
        workspace_id=uuid.uuid4(),
        role=AppRole.admin,
        locale="en",
        timezone="UTC",
        memberships=[],
        workspace_plan="pro",
        completed_review_runs=939,
        review_run_limit=None,
    )

    assert response.completed_review_runs == 939
    assert response.review_run_limit is None


@pytest.mark.asyncio
async def test_me_response_free_at_limit():
    """Free workspace at limit."""
    response = MeResponse(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        status=UserStatus.active,
        platform_role=None,
        workspace_id=uuid.uuid4(),
        role=AppRole.admin,
        locale="en",
        timezone="UTC",
        memberships=[],
        workspace_plan="free",
        completed_review_runs=25,
        review_run_limit=25,
    )

    assert response.completed_review_runs == 25
    assert response.review_run_limit == 25
    assert response.completed_review_runs >= response.review_run_limit