# backend/tests/unit/test_items.py
"""Item schemas + service helpers — tests/unit/ only."""
import pytest
from pydantic import ValidationError

from app.constants.enums import ItemStatus
from app.schemas.items import ItemCreate, ItemUpdate
from app.services.items import default_item_status


def test_item_create_requires_name():
    with pytest.raises(ValidationError):
        ItemCreate(name="")


def test_item_update_optional_fields():
    payload = ItemUpdate()
    assert payload.name is None
    assert payload.status is None


def test_default_item_status():
    assert default_item_status() == ItemStatus.draft
