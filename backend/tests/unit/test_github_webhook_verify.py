# backend/tests/unit/test_github_webhook_verify.py
"""GitHub webhook HMAC verification — R0."""
import hashlib
import hmac

from app.integrations.github_webhook import verify_github_signature


def test_verify_github_signature_accepts_valid_signature():
    secret = "local-webhook-secret"
    payload = b'{"action":"created"}'
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    signature = f"sha256={digest}"

    assert verify_github_signature(payload, signature, secret) is True


def test_verify_github_signature_rejects_invalid_signature():
    assert verify_github_signature(b"{}", "sha256=deadbeef", "secret") is False


def test_verify_github_signature_rejects_missing_prefix():
    assert verify_github_signature(b"{}", "deadbeef", "secret") is False
