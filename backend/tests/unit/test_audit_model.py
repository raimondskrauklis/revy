# backend/tests/unit/test_audit_model.py
"""api_audit ORM metadata — AUDIT.md."""
from app.models.audit_log import AuditLogORM


def test_audit_log_table_metadata():
    table = AuditLogORM.__table__

    assert table.name == "api_audit"
    assert "actor_user_id" in table.columns
    assert "impersonator_user_id" in table.columns
    assert "workspace_id" in table.columns
    assert "action" in table.columns
    assert "metadata" in table.columns
    assert table.columns["metadata"].nullable is False

    index_names = {index.name for index in table.indexes}
    assert "ix_api_audit_workspace_id_created_at" in index_names
    assert "ix_api_audit_created_at" in index_names
