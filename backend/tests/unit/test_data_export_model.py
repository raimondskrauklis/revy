# backend/tests/unit/test_data_export_model.py
"""DataExportJobORM and ExportJobStatus — W6 lifecycle."""
import uuid
from datetime import UTC, datetime

from app.constants.enums import ExportJobStatus
from app.models.data_export_job import DataExportJobORM


def test_export_job_status_values():
    assert ExportJobStatus.pending.value == "pending"
    assert ExportJobStatus.processing.value == "processing"
    assert ExportJobStatus.completed.value == "completed"
    assert ExportJobStatus.failed.value == "failed"


def test_data_export_job_orm_defaults():
    user_id = uuid.uuid4()
    job = DataExportJobORM(user_id=user_id, status=ExportJobStatus.pending)

    assert job.user_id == user_id
    assert job.status == ExportJobStatus.pending
    assert job.storage_key is None
    assert job.error_message is None
    assert job.file_size_bytes is None
    assert job.expires_at is None
    assert job.completed_at is None


def test_data_export_job_orm_completed_fields():
    user_id = uuid.uuid4()
    completed_at = datetime.now(UTC)
    expires_at = datetime.now(UTC)
    job = DataExportJobORM(
        user_id=user_id,
        status=ExportJobStatus.completed,
        storage_key="job.zip",
        file_size_bytes=1024,
        completed_at=completed_at,
        expires_at=expires_at,
    )

    assert job.status == ExportJobStatus.completed
    assert job.storage_key == "job.zip"
    assert job.file_size_bytes == 1024
    assert job.completed_at == completed_at
    assert job.expires_at == expires_at
