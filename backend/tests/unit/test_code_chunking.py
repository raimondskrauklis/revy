# backend/tests/unit/test_code_chunking.py
"""Code chunking service — R3."""
from app.services.code_chunking import chunk_file_content, should_index_file


def test_should_index_file_skips_node_modules():
    assert should_index_file("node_modules/pkg/index.js") is False
    assert should_index_file("src/main.py") is True


def test_chunk_file_content_splits_long_files():
    content = "\n".join(f"line {i}" for i in range(500))
    chunks = chunk_file_content("src/main.py", content)
    assert len(chunks) > 1
    assert chunks[0].file_path == "src/main.py"
    assert all(len(chunk.content) <= 2000 for chunk in chunks)
