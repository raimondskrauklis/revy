# backend/tests/unit/test_bootstrap_config.py
"""Bootstrap super-admin startup guard — USER_PROVISIONING P3."""
from unittest.mock import AsyncMock, patch

import pytest

from app.core.bootstrap import BootstrapConfigError, validate_bootstrap_super_admin_config


@pytest.mark.asyncio
async def test_bootstrap_guard_skipped_in_test_environment():
    session = AsyncMock()
    with patch("app.core.bootstrap.settings") as mock_settings:
        mock_settings.environment = "test"
        mock_settings.bootstrap_super_admin_email = "admin@example.com"
        await validate_bootstrap_super_admin_config(session)
    session.scalar.assert_not_awaited()


@pytest.mark.asyncio
async def test_bootstrap_guard_skipped_when_email_unset():
    session = AsyncMock()
    with patch("app.core.bootstrap.settings") as mock_settings:
        mock_settings.environment = "production"
        mock_settings.bootstrap_super_admin_email = None
        await validate_bootstrap_super_admin_config(session)
    session.scalar.assert_not_awaited()


@pytest.mark.asyncio
async def test_bootstrap_guard_passes_when_seed_exists():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=object())
    with patch("app.core.bootstrap.settings") as mock_settings:
        mock_settings.environment = "production"
        mock_settings.bootstrap_super_admin_email = "admin@example.com"
        await validate_bootstrap_super_admin_config(session)


@pytest.mark.asyncio
async def test_bootstrap_guard_warns_in_development():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    with patch("app.core.bootstrap.settings") as mock_settings:
        mock_settings.environment = "development"
        mock_settings.bootstrap_super_admin_email = "admin@example.com"
        await validate_bootstrap_super_admin_config(session)


@pytest.mark.asyncio
async def test_bootstrap_guard_raises_in_production():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    with patch("app.core.bootstrap.settings") as mock_settings:
        mock_settings.environment = "production"
        mock_settings.bootstrap_super_admin_email = "admin@example.com"
        with pytest.raises(BootstrapConfigError):
            await validate_bootstrap_super_admin_config(session)


@pytest.mark.asyncio
async def test_bootstrap_guard_raises_in_staging():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    with patch("app.core.bootstrap.settings") as mock_settings:
        mock_settings.environment = "staging"
        mock_settings.bootstrap_super_admin_email = "admin@example.com"
        with pytest.raises(BootstrapConfigError):
            await validate_bootstrap_super_admin_config(session)
