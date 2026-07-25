# backend/app/services/data_export.py
"""User data export jobs — ACCOUNT_LIFECYCLE.md."""
from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import ExportJobStatus
from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.data_export_job import DataExportJobORM
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.services.audit_service import record_audit


def _export_storage_dir() -> Path:
    path = Path(settings.export_storage_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def export_file_path(job_id: UUID) -> Path:
    return _export_storage_dir() / f"{job_id}.zip"


async def _get_active_job(session: AsyncSession, *, user_id: UUID) -> DataExportJobORM | None:
    return await session.scalar(
        select(DataExportJobORM)
        .where(
            DataExportJobORM.user_id == user_id,
            DataExportJobORM.status.in_(
                (ExportJobStatus.pending, ExportJobStatus.processing),
            ),
        )
        .with_for_update()
    )


async def create_export_job(
    session: AsyncSession,
    *,
    user_id: UUID,
    impersonator_user_id: UUID | None = None,
) -> DataExportJobORM:
    active = await _get_active_job(session, user_id=user_id)
    if active is not None:
        raise ConflictError(
            message="An export is already in progress",
            error_code="export_in_progress",
        )

    job = DataExportJobORM(user_id=user_id, status=ExportJobStatus.pending)
    session.add(job)
    await session.flush()

    await record_audit(
        session,
        actor_user_id=user_id,
        impersonator_user_id=impersonator_user_id,
        workspace_id=None,
        action="user.export_requested",
        resource_type="data_export_job",
        resource_id=str(job.id),
    )
    return job


async def get_export_job_for_user(
    session: AsyncSession,
    *,
    job_id: UUID,
    user_id: UUID,
) -> DataExportJobORM:
    job = await session.get(DataExportJobORM, job_id)
    if job is None or job.user_id != user_id:
        raise NotFoundError("Export job not found")
    return job


async def build_export_payload(session: AsyncSession, *, user_id: UUID) -> dict:
    user = await session.get(UserORM, user_id)
    if user is None:
        raise NotFoundError("User not found")

    membership_rows = (
        await session.execute(
            select(WorkspaceMembershipORM, WorkspaceORM)
            .join(WorkspaceORM, WorkspaceORM.id == WorkspaceMembershipORM.workspace_id)
            .where(WorkspaceMembershipORM.user_id == user_id)
            .order_by(WorkspaceORM.name.asc())
        )
    ).all()

    memberships = [
        {
            "workspace_id": str(membership.workspace_id),
            "workspace_name": workspace.name,
            "workspace_slug": workspace.slug,
            "role": membership.role.value,
        }
        for membership, workspace in membership_rows
    ]

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "locale": user.locale,
            "timezone": user.timezone,
            "status": user.status.value,
        },
        "memberships": memberships,
        "exported_at": datetime.now(UTC).isoformat(),
    }


def write_export_zip(*, job_id: UUID, payload: dict) -> tuple[str, int]:
    path = export_file_path(job_id)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("export.json", json.dumps(payload, indent=2, default=str))
    size = path.stat().st_size
    return f"{job_id}.zip", size


async def mark_processing(session: AsyncSession, *, job_id: UUID) -> DataExportJobORM:
    job = await session.get(DataExportJobORM, job_id)
    if job is None:
        raise NotFoundError("Export job not found")
    job.status = ExportJobStatus.processing
    await session.flush()
    return job


async def mark_completed(
    session: AsyncSession,
    *,
    job_id: UUID,
    storage_key: str,
    file_size_bytes: int,
) -> DataExportJobORM:
    job = await session.get(DataExportJobORM, job_id)
    if job is None:
        raise NotFoundError("Export job not found")

    completed_at = datetime.now(UTC)
    job.status = ExportJobStatus.completed
    job.storage_key = storage_key
    job.file_size_bytes = file_size_bytes
    job.completed_at = completed_at
    job.expires_at = completed_at + timedelta(days=settings.export_ttl_days)
    await session.flush()
    return job


async def mark_failed(
    session: AsyncSession,
    *,
    job_id: UUID,
    error_message: str,
) -> DataExportJobORM:
    job = await session.get(DataExportJobORM, job_id)
    if job is None:
        raise NotFoundError("Export job not found")

    job.status = ExportJobStatus.failed
    job.error_message = error_message[:2000]
    job.completed_at = datetime.now(UTC)
    await session.flush()
    return job


def resolve_download_path(job: DataExportJobORM) -> Path:
    if job.status != ExportJobStatus.completed:
        raise ValidationError(message="Export is not ready for download")
    if job.expires_at is not None and job.expires_at <= datetime.now(UTC):
        raise ForbiddenError(
            message="Export download has expired",
            error_code="export_expired",
        )
    if not job.storage_key:
        raise NotFoundError("Export file not found")

    path = _export_storage_dir() / job.storage_key
    if not path.is_file():
        raise NotFoundError("Export file not found")
    return path
