# backend/tests/unit/test_pagination.py
"""Cursor encode/decode — pagination.py."""
from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.core.pagination import (
    InvalidCursorError,
    decode_cursor,
    decode_cursor_payload,
    encode_cursor,
    encode_cursor_payload,
)


def test_encode_decode_cursor_roundtrip():
    created = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    row_id = UUID("018f1234-5678-7abc-8def-123456789abc")
    token = encode_cursor(created, row_id)
    decoded_created, decoded_id = decode_cursor(token)
    assert decoded_id == row_id
    assert decoded_created == created


def test_decode_cursor_invalid_raises():
    with pytest.raises(InvalidCursorError):
        decode_cursor("not-a-valid-cursor")


def test_encode_decode_payload_roundtrip():
    payload = {"risk_score": 0.42, "lot_id": "abc"}
    token = encode_cursor_payload(payload)
    assert decode_cursor_payload(token) == payload
