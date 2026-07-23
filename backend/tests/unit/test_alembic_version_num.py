# backend/tests/unit/test_alembic_version_num.py
from pathlib import Path

from app.core.alembic_postgresql import ALEMBIC_VERSION_NUM_LENGTH


def test_revision_ids_fit_alembic_version_column():
    versions_dir = Path(__file__).resolve().parents[2] / "alembic" / "versions"
    revision_ids = []
    for path in versions_dir.glob("*.py"):
        if path.name.startswith("."):
            continue
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("revision = "):
                revision_ids.append(line.split("=", 1)[1].strip().strip('"'))

    assert revision_ids, "expected at least one migration revision id"
    for rev_id in revision_ids:
        assert len(rev_id) <= ALEMBIC_VERSION_NUM_LENGTH, rev_id
