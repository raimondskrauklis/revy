# backend/tests/unit/test_engineering_context_config.py
"""RCX P0 — review prompt cap settings defaults."""
from app.core.config import Settings, reset_revy_llm_provider_alias_logged


def test_engineering_context_cap_defaults():
    reset_revy_llm_provider_alias_logged()
    settings = Settings(
        environment="test",
        database_url="postgresql+asyncpg://u@localhost/db",
        redis_url="redis://localhost",
        secret_key="test",
        allowed_origins="http://localhost",
        keycloak_url="http://localhost",
        keycloak_realm="revy",
        keycloak_client_id="revy-api",
        keycloak_client_secret="secret",
    )
    assert settings.revy_diff_max_bytes == 524288
    assert settings.revy_engineering_context_max_bytes == 32768
    assert settings.revy_pr_body_max_bytes == 4096
