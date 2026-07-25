# backend/tests/unit/test_data_export_service.py
"""Data export service — ACCOUNT_LIFECYCLE.md."""
import json
import uuid
import zipfile
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import AppRole, ExportJobStatus, UserStatus, WorkspaceStatus
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.data_export_job import DataExportJobORM
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.services.data_export import (
    build_export_payload,
    create_export_job,
    get_export_job_for_user,
    mark_completed,
    mark_failed,
    mark_processing,
    resolve_download_path,
    write_export_zip,
)


@pytest.mark.asyncio
async def test_create_export_job_persists_and_audits():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    user_id = uuid.uuid4()
    with patch("app.services.data_export.record_audit", new_callable=AsyncMock) as record:
        job = await create_export_job(session, user_id=user_id)

    session.add.assert_called_once()
    record.assert_awaited_once()
    assert job.user_id == user_id
    assert job.status == ExportJobStatus.pending


@pytest.mark.asyncio
async def test_create_export_job_blocks_active_job():
    session = AsyncMock()
    active = DataExportJobORM(user_id=uuid.uuid4(), status=ExportJobStatus.processing)
    session.scalar = AsyncMock(return_value=active)

    with pytest.raises(ConflictError) as exc_info:
        await create_export_job(session, user_id=uuid.uuid4())

    assert exc_info.value.error_code == "export_in_progress"


@pytest.mark.asyncio
async def test_build_export_payload_includes_user_and_memberships():
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    user = UserORM(
        keycloak_user_id="kc-1",
        email="user@example.com",
        full_name="User",
        status=UserStatus.active,
    )
    user.id = user_id
    workspace = WorkspaceORM(slug="acme", name="Acme", status=WorkspaceStatus.active)
    workspace.id = workspace_id
    membership = WorkspaceMembershipORM(
        user_id=user_id,
        workspace_id=workspace_id,
        role=AppRole.admin,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=user)
    result = MagicMock()
    result.all.return_value = [(membership, workspace)]
    session.execute = AsyncMock(return_value=result)

    payload = await build_export_payload(session, user_id=user_id)

    assert payload["user"]["email"] == "user@example.com"
    assert len(payload["memberships"]) == 1
    assert payload["memberships"][0]["workspace_slug"] == "acme"


def test_write_export_zip_creates_json_archive(tmp_path):
    job_id = uuid.uuid4()
    with patch("app.services.data_export._export_storage_dir", return_value=tmp_path):
        storage_key, size = write_export_zip(
            job_id=job_id,
            payload={"user": {"email": "user@example.com"}},
        )

    assert storage_key == f"{job_id}.zip"
    assert size > 0
    with zipfile.ZipFile(tmp_path / storage_key) as archive:
        data = json.loads(archive.read("export.json"))
    assert data["user"]["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_mark_completed_sets_expiry():
    job_id = uuid.uuid4()
    job = DataExportJobORM(user_id=uuid.uuid4(), status=ExportJobStatus.processing)
    job.id = job_id

    session = AsyncMock()
    session.get = AsyncMock(return_value=job)
    session.flush = AsyncMock()

    with patch("app.services.data_export.settings.export_ttl_days", 7):
        updated = await mark_completed(
            session,
            job_id=job_id,
            storage_key="export.zip",
            file_size_bytes=512,
        )

    assert updated.status == ExportJobStatus.completed
    assert updated.storage_key == "export.zip"
    assert updated.expires_at is not None
    assert updated.completed_at is not None


@pytest.mark.asyncio
async def test_mark_failed_sets_error_message():
    job = DataExportJobORM(user_id=uuid.uuid4(), status=ExportJobStatus.processing)
    session = AsyncMock()
    session.get = AsyncMock(return_value=job)
    session.flush = AsyncMock()

    updated = await mark_failed(session, job_id=job.id, error_message="disk full")

    assert updated.status == ExportJobStatus.failed
    assert updated.error_message == "disk full"


@pytest.mark.asyncio
async def test_get_export_job_for_user_rejects_other_owner():
    job = DataExportJobORM(user_id=uuid.uuid4(), status=ExportJobStatus.pending)
    job.id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=job)

    with pytest.raises(NotFoundError):
        await get_export_job_for_user(session, job_id=job.id, user_id=uuid.uuid4())


def test_resolve_download_path_rejects_expired_job(tmp_path):
    job = DataExportJobORM(
        user_id=uuid.uuid4(),
        status=ExportJobStatus.completed,
        storage_key="done.zip",
        expires_at=datetime(2020, 1, 1, tzinfo=UTC),
    )

    with patch("app.services.data_export._export_storage_dir", return_value=tmp_path):
        with pytest.raises(ForbiddenError) as exc_info:
            resolve_download_path(job)

    assert exc_info.value.error_code == "export_expired"


def test_resolve_download_path_returns_existing_file(tmp_path):
    job_id = uuid.uuid4()
    storage_key = f"{job_id}.zip"
    path = tmp_path / storage_key
    path.write_bytes(b"zip")

    job = DataExportJobORM(
        user_id=uuid.uuid4(),
        status=ExportJobStatus.completed,
        storage_key=storage_key,
        expires_at=datetime(2099, 1, 1, tzinfo=UTC),
    )

    with patch("app.services.data_export._export_storage_dir", return_value=tmp_path):
        resolved = resolve_download_path(job)

    assert resolved == path


@pytest.mark.asyncio
async def test_mark_processing_updates_status():
    job = DataExportJobORM(user_id=uuid.uuid4(), status=ExportJobStatus.pending)
    session = AsyncMock()
    session.get = AsyncMock(return_value=job)
    session.flush = AsyncMock()

    updated = await mark_processing(session, job_id=job.id)

    assert updated.status == ExportJobStatus.processing
