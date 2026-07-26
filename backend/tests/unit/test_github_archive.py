# backend/tests/unit/test_github_archive.py
"""GitHub tarball archive helpers — R3."""
import io
import tarfile

from app.integrations.github_archive import extract_tarball
from app.services.code_chunking import should_index_file


def test_extract_tarball_creates_root(tmp_path):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        data = b"print('hi')\n"
        info = tarfile.TarInfo(name="repo-main/src/main.py")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    root = extract_tarball(buffer.getvalue(), tmp_path / "extract")
    assert (root / "src" / "main.py").exists()


def test_should_index_file_matches_chunking_rules():
    assert should_index_file("src/app.py") is True
