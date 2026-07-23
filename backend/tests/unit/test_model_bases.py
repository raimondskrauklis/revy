# backend/tests/unit/test_model_bases.py
"""AuditableModel soft delete + TimestampedModel updated_at."""
from datetime import UTC, datetime
from uuid import uuid4

from app.models.base import AuditableModel, TimestampedModel, utc_now


class _SampleTimestamped(TimestampedModel):
    __tablename__ = "test_timestamped_sample"
    __abstract__ = True


class _SampleAuditable(AuditableModel):
    __tablename__ = "test_auditable_sample"
    __abstract__ = True


def test_utc_now_is_timezone_aware():
    now = utc_now()
    assert now.tzinfo is not None


def test_auditable_soft_delete_and_restore():
    row = _SampleAuditable()
    assert row.is_deleted is False
    actor = uuid4()
    row.soft_delete(deleted_by_id=actor)
    assert row.is_deleted is True
    assert row.deleted_at is not None
    assert row.updated_by_id == actor
    row.restore(restored_by_id=actor)
    assert row.is_deleted is False
    assert row.deleted_at is None


def test_timestamped_before_update_sets_updated_at():
    row = _SampleTimestamped()
    past = datetime(2020, 1, 1, tzinfo=UTC)
    row.updated_at = past
    from app.models.base import _touch_updated_at

    _touch_updated_at(None, None, row)
    assert row.updated_at > past
