# backend/tests/unit/test_github_installations.py
"""GitHub installation service — REVY_PRODUCT_SLICE.md."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.constants.enums import GitHubAccountType, GitHubInstallationStatus
from app.core.exceptions import ConflictError
from app.core.pagination import CursorParams
from app.models.github_installation import GitHubInstallationORM
from app.schemas.github_installation import GitHubInstallationCreate
from app.services.github_installations import (
    bind_github_installation,
    create_github_installation,
    list_github_installations,
    verify_granted_repositories,
)


@pytest.mark.asyncio
async def test_create_github_installation_persists_row():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[MagicMock(), None])
    session.add = MagicMock()
    session.flush = AsyncMock()

    payload = GitHubInstallationCreate(
        github_installation_id=12345,
        account_login="acme-corp",
        account_type=GitHubAccountType.organization,
        account_id=99,
        permissions_snapshot={"contents": "read"},
    )

    row = await create_github_installation(session, workspace_id=workspace_id, payload=payload)

    session.add.assert_called_once()
    assert row.workspace_id == workspace_id
    assert row.github_installation_id == 12345
    assert row.account_login == "acme-corp"
    assert row.status == GitHubInstallationStatus.active


@pytest.mark.asyncio
async def test_create_github_installation_rejects_duplicate():
    workspace_id = uuid.uuid4()
    existing = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme-corp",
        account_type=GitHubAccountType.organization,
        account_id=99,
        status=GitHubInstallationStatus.active,
    )

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[MagicMock(), existing])

    payload = GitHubInstallationCreate(
        github_installation_id=12345,
        account_login="acme-corp",
        account_type=GitHubAccountType.organization,
        account_id=99,
    )

    with pytest.raises(ConflictError):
        await create_github_installation(session, workspace_id=workspace_id, payload=payload)


@pytest.mark.asyncio
async def test_create_github_installation_maps_integrity_error_to_conflict():
    workspace_id = uuid.uuid4()
    other_workspace_id = uuid.uuid4()
    raced = GitHubInstallationORM(
        workspace_id=other_workspace_id,
        github_installation_id=12345,
        account_login="acme-corp",
        account_type=GitHubAccountType.organization,
        account_id=99,
        status=GitHubInstallationStatus.active,
    )

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[MagicMock(), None, raced])
    session.add = MagicMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock(side_effect=IntegrityError("insert", {}, Exception("unique")))

    payload = GitHubInstallationCreate(
        github_installation_id=12345,
        account_login="acme-corp",
        account_type=GitHubAccountType.organization,
        account_id=99,
    )

    with pytest.raises(ConflictError, match="linked to another workspace"):
        await create_github_installation(session, workspace_id=workspace_id, payload=payload)

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_github_installations_returns_cursor_page():
    workspace_id = uuid.uuid4()
    row = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=1,
        account_login="solo-dev",
        account_type=GitHubAccountType.user,
        account_id=2,
        status=GitHubInstallationStatus.active,
    )
    row.id = uuid.uuid4()
    row.created_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)

    session = AsyncMock()
    session.scalars = AsyncMock(return_value=[row])

    page = await list_github_installations(
        session,
        workspace_id=workspace_id,
        params=CursorParams(limit=50),
    )

    assert len(page.items) == 1
    assert page.items[0].account_login == "solo-dev"
    assert page.cursor.has_next is False
    assert page.items[0].verified_at is None


@pytest.mark.asyncio
async def test_bind_github_installation_inserts_unverified_and_enqueues():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    workspace = MagicMock()
    session.scalar = AsyncMock(side_effect=[workspace, None])
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch(
        "app.services.github_installations.workspace_has_feature",
        return_value=True,
    ):
        row = await bind_github_installation(
            session,
            workspace_id=workspace_id,
            github_installation_id=12345,
            account_login="acme-corp",
            account_type=GitHubAccountType.organization,
            account_id=99,
        )

    session.add.assert_called_once()
    assert row.verified_at is None
    assert row.status == GitHubInstallationStatus.active


@pytest.mark.asyncio
async def test_bind_github_installation_same_workspace_is_idempotent():
    workspace_id = uuid.uuid4()
    existing = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="old-login",
        account_type=GitHubAccountType.organization,
        account_id=99,
        status=GitHubInstallationStatus.active,
    )
    existing.id = uuid.uuid4()
    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[MagicMock(), existing])
    session.flush = AsyncMock()

    with patch(
        "app.services.github_installations.workspace_has_feature",
        return_value=True,
    ):
        row = await bind_github_installation(
            session,
            workspace_id=workspace_id,
            github_installation_id=12345,
            account_login="new-login",
            account_type=GitHubAccountType.organization,
            account_id=99,
        )

    assert row is existing
    assert row.account_login == "new-login"


@pytest.mark.asyncio
async def test_bind_github_installation_other_workspace_conflicts():
    workspace_id = uuid.uuid4()
    existing = GitHubInstallationORM(
        workspace_id=uuid.uuid4(),
        github_installation_id=12345,
        account_login="acme-corp",
        account_type=GitHubAccountType.organization,
        account_id=99,
        status=GitHubInstallationStatus.active,
    )
    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[MagicMock(), existing])

    with patch(
        "app.services.github_installations.workspace_has_feature",
        return_value=True,
    ):
        with pytest.raises(ConflictError, match="linked to another workspace"):
            await bind_github_installation(
                session,
                workspace_id=workspace_id,
                github_installation_id=12345,
                account_login="acme-corp",
                account_type=GitHubAccountType.organization,
                account_id=99,
            )


def _unverified_row(workspace_id: uuid.UUID) -> GitHubInstallationORM:
    row = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme-corp",
        account_type=GitHubAccountType.organization,
        account_id=99,
        status=GitHubInstallationStatus.active,
    )
    row.id = uuid.uuid4()
    row.verified_at = None
    return row


@pytest.mark.asyncio
async def test_verify_granted_repositories_sets_verified_at_when_repos_exist():
    session = AsyncMock()
    session.flush = AsyncMock()
    row = _unverified_row(uuid.uuid4())
    client = MagicMock()

    with patch(
        "app.services.github_installations.list_installation_repositories",
        AsyncMock(return_value=[{"id": 1, "full_name": "acme/app"}]),
    ):
        result = await verify_granted_repositories(session, installation=row, client=client)

    assert result.verified_at is not None
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_granted_repositories_empty_list_leaves_verified_at_null():
    session = AsyncMock()
    session.flush = AsyncMock()
    row = _unverified_row(uuid.uuid4())
    client = MagicMock()

    with patch(
        "app.services.github_installations.list_installation_repositories",
        AsyncMock(return_value=[]),
    ):
        result = await verify_granted_repositories(session, installation=row, client=client)

    assert result.verified_at is None
    session.flush.assert_awaited_once()
