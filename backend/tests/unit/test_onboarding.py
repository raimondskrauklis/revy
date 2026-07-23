# backend/tests/unit/test_onboarding.py
"""Registration config — USER_REGISTRATION.md."""
from unittest.mock import patch

import pytest

from app.constants.enums import UserStatus
from app.services.onboarding import (
    resolve_initial_user_status,
    should_auto_provision_user,
)


@pytest.mark.parametrize(
    ("admin_approval", "profile_form", "email_verified", "expected"),
    [
        (False, False, False, UserStatus.pending_email_verification),
        (False, False, True, UserStatus.pending_profile),
        (False, True, True, UserStatus.pending_profile),
        (True, False, True, UserStatus.pending_approval),
        (True, True, True, UserStatus.pending_profile),
    ],
)
def test_resolve_initial_user_status(admin_approval, profile_form, email_verified, expected):
    with (
        patch("app.services.onboarding.settings.registration_require_admin_approval", admin_approval),
        patch("app.services.onboarding.settings.registration_require_profile_form", profile_form),
    ):
        assert resolve_initial_user_status(email_verified=email_verified) == expected


def test_should_auto_provision_only_open_mode():
    with (
        patch("app.services.onboarding.settings.registration_require_admin_approval", False),
        patch("app.services.onboarding.settings.registration_require_profile_form", False),
    ):
        assert should_auto_provision_user(email_verified=True) is True
        assert should_auto_provision_user(email_verified=False) is False

    with patch("app.services.onboarding.settings.registration_require_profile_form", True):
        assert should_auto_provision_user(email_verified=True) is False
