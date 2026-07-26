# backend/tests/unit/test_keycloak_webhook_verify.py
"""Keycloak webhook secret verification — USER_PROVISIONING P1."""
import base64

from app.integrations.keycloak_webhook import verify_keycloak_webhook_secret


def test_verify_keycloak_webhook_secret_accepts_matching_header():
    assert verify_keycloak_webhook_secret("super-secret", "super-secret") is True


def test_verify_keycloak_webhook_secret_rejects_wrong_header():
    assert verify_keycloak_webhook_secret("wrong", "super-secret") is False


def test_verify_keycloak_webhook_secret_rejects_missing_header():
    assert verify_keycloak_webhook_secret(None, "super-secret") is False


def test_verify_keycloak_webhook_basic_auth_accepts_matching_password():
    from app.integrations.keycloak_webhook import verify_keycloak_webhook_basic_auth

    token = base64.b64encode(b"revy:super-secret").decode()
    assert verify_keycloak_webhook_basic_auth(f"Basic {token}", "super-secret") is True


def test_verify_keycloak_webhook_basic_auth_rejects_wrong_password():
    from app.integrations.keycloak_webhook import verify_keycloak_webhook_basic_auth

    token = base64.b64encode(b"revy:wrong").decode()
    assert verify_keycloak_webhook_basic_auth(f"Basic {token}", "super-secret") is False
