# backend/tests/unit/test_keycloak_issuer.py
"""KEYCLOAK_ISSUER vs internal KEYCLOAK_URL — production docker pattern."""
from unittest.mock import patch

from app.core.config import Settings


def test_keycloak_token_issuer_defaults_to_keycloak_url():
    settings = Settings(
        environment="development",
        database_url="postgresql+asyncpg://localhost/revy",
        redis_url="redis://localhost:6379/0",
        secret_key="test",
        allowed_origins="http://localhost:5173",
        keycloak_url="http://localhost:8080",
        keycloak_realm="revy",
        keycloak_client_id="revy-api",
        keycloak_client_secret="secret",
    )

    assert settings.keycloak_token_issuer == "http://localhost:8080/realms/revy"


def test_keycloak_token_issuer_uses_public_override():
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://localhost/revy",
        redis_url="redis://localhost:6379/0",
        secret_key="test",
        allowed_origins="https://revy.createit.digital",
        keycloak_url="http://keycloak:8080",
        keycloak_realm="revy",
        keycloak_client_id="revy-api",
        keycloak_client_secret="secret",
        keycloak_issuer="https://auth.revy.createit.digital/realms/revy",
    )

    assert settings.keycloak_token_issuer == "https://auth.revy.createit.digital/realms/revy"


def test_jwks_client_issuer_uses_keycloak_token_issuer():
    from app.core.jwks import jwks_client

    with (
        patch("app.core.jwks.settings.keycloak_url", "http://keycloak:8080"),
        patch("app.core.jwks.settings.keycloak_realm", "revy"),
        patch(
            "app.core.jwks.settings.keycloak_issuer",
            "https://auth.revy.createit.digital/realms/revy",
        ),
    ):
        assert jwks_client.issuer == "https://auth.revy.createit.digital/realms/revy"
