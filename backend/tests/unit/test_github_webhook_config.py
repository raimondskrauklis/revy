# backend/tests/unit/test_github_webhook_config.py
"""GitHub webhook settings — R0."""
from app.core.config import Settings


def test_github_webhooks_enabled_requires_secret():
    settings = Settings(
        environment="test",
        database_url="postgresql+asyncpg://u:p@localhost/db",
        redis_url="redis://localhost:6379/0",
        secret_key="secret",
        allowed_origins="http://localhost:5173",
        keycloak_url="http://localhost:8080",
        keycloak_realm="revy",
        keycloak_client_id="revy-api",
        keycloak_client_secret="secret",
        github_webhook_secret="whsec_test",
    )
    assert settings.github_webhooks_enabled is True


def test_github_webhooks_disabled_when_secret_empty():
    settings = Settings(
        environment="test",
        database_url="postgresql+asyncpg://u:p@localhost/db",
        redis_url="redis://localhost:6379/0",
        secret_key="secret",
        allowed_origins="http://localhost:5173",
        keycloak_url="http://localhost:8080",
        keycloak_realm="revy",
        keycloak_client_id="revy-api",
        keycloak_client_secret="secret",
        github_webhook_secret="",
    )
    assert settings.github_webhooks_enabled is False
