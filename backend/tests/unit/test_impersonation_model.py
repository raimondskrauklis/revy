# backend/tests/unit/test_impersonation_model.py
"""ImpersonationSessionORM — W7."""
import uuid
from datetime import UTC, datetime

from app.models.impersonation_session import ImpersonationSessionORM


def test_impersonation_session_orm_defaults():
    actor_id = uuid.uuid4()
    target_id = uuid.uuid4()
    session = ImpersonationSessionORM(
        actor_user_id=actor_id,
        target_user_id=target_id,
        reason="Support ticket #12345 — reproducing billing issue",
    )

    assert session.actor_user_id == actor_id
    assert session.target_user_id == target_id
    assert session.reason.startswith("Support ticket")
    assert session.ended_at is None


def test_impersonation_session_orm_ended():
    actor_id = uuid.uuid4()
    target_id = uuid.uuid4()
    ended_at = datetime.now(UTC)
    session = ImpersonationSessionORM(
        actor_user_id=actor_id,
        target_user_id=target_id,
        reason="Debugging workspace access for customer",
        ended_at=ended_at,
    )

    assert session.ended_at == ended_at
