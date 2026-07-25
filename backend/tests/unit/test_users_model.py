# backend/tests/unit/test_users_model.py
"""User ORM columns — ME_ENDPOINT.md W1."""
from app.models.users import UserORM


def test_user_orm_has_locale_and_timezone_defaults():
    columns = UserORM.__table__.columns

    locale = columns["locale"]
    timezone = columns["timezone"]

    assert str(locale.type) == "VARCHAR(16)"
    assert locale.nullable is False
    assert locale.server_default is not None
    assert locale.server_default.arg == "en"

    assert str(timezone.type) == "VARCHAR(64)"
    assert timezone.nullable is False
    assert timezone.server_default is not None
    assert timezone.server_default.arg == "UTC"

    assert UserORM.locale.property.columns[0].default.arg == "en"
    assert UserORM.timezone.property.columns[0].default.arg == "UTC"
