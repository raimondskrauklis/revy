# backend/tests/unit/test_billing_config.py
"""Stripe billing settings — defaults and env wiring."""
from pathlib import Path

from app.core.config import Settings


def _base_settings_kwargs() -> dict:
    return {
        "environment": "development",
        "database_url": "postgresql+asyncpg://localhost/revy",
        "redis_url": "redis://localhost:6379/0",
        "secret_key": "test",
        "allowed_origins": "http://localhost:5173",
        "keycloak_url": "http://localhost:8080",
        "keycloak_realm": "revy",
        "keycloak_client_id": "revy-api",
        "keycloak_client_secret": "secret",
    }


def test_stripe_disabled_by_default():
    settings = Settings(**_base_settings_kwargs())

    assert settings.stripe_enabled is False
    assert settings.stripe_secret_key is None
    assert settings.stripe_webhook_secret is None
    assert settings.stripe_price_pro is None


def test_stripe_settings_load_from_env():
    settings = Settings(
        **_base_settings_kwargs(),
        stripe_enabled=True,
        stripe_secret_key="sk_test_123",
        stripe_webhook_secret="whsec_123",
        stripe_price_pro="price_pro_test",
        stripe_checkout_success_url="https://example.com/success",
        stripe_checkout_cancel_url="https://example.com/cancel",
    )

    assert settings.stripe_enabled is True
    assert settings.stripe_secret_key == "sk_test_123"
    assert settings.stripe_webhook_secret == "whsec_123"
    assert settings.stripe_price_pro == "price_pro_test"
    assert settings.stripe_checkout_success_url == "https://example.com/success"
    assert settings.stripe_checkout_cancel_url == "https://example.com/cancel"


def test_stripe_dependency_in_requirements():
    requirements_path = Path(__file__).resolve().parents[2] / "requirements" / "base.txt"
    contents = requirements_path.read_text(encoding="utf-8")

    assert "stripe>=" in contents
