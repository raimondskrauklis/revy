# backend/tests/unit/test_jwks.py
"""JWKS signing-key resolution — Keycloak kid lookup and sig/enc filtering."""
from __future__ import annotations

import json

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm
from jwt.exceptions import PyJWKSetError

from app.core.jwks import (
    JwkSigningKeyNotFoundError,
    signing_key_from_jwt,
    signing_keys_from_jwks,
)


def _rsa_jwk(*, kid: str, use: str = "sig", alg: str = "RS256") -> tuple[dict, bytes]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    jwk_dict = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk_dict.update({"kid": kid, "use": use, "alg": alg})
    return jwk_dict, private_pem


def test_signing_keys_from_jwks_filters_encryption_keys():
    sig_jwk, _ = _rsa_jwk(kid="sig-kid", use="sig")
    enc_jwk, _ = _rsa_jwk(kid="enc-kid", use="enc", alg="RSA-OAEP")

    keys = signing_keys_from_jwks({"keys": [sig_jwk, enc_jwk]})

    assert [key.key_id for key in keys] == ["sig-kid"]


def test_signing_keys_from_jwks_rejects_empty_signing_set():
    enc_jwk, _ = _rsa_jwk(kid="enc-kid", use="enc", alg="RS256")

    with pytest.raises(PyJWKSetError, match="signing keys"):
        signing_keys_from_jwks({"keys": [enc_jwk]})


def test_signing_key_from_jwt_resolves_signing_kid():
    sig_jwk, private_pem = _rsa_jwk(kid="sig-kid")
    enc_jwk, _ = _rsa_jwk(kid="enc-kid", use="enc", alg="RSA-OAEP")
    token = jwt.encode(
        {"sub": "user-1"},
        private_pem,
        algorithm="RS256",
        headers={"kid": "sig-kid"},
    )

    signing_key = signing_key_from_jwt({"keys": [sig_jwk, enc_jwk]}, token)

    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )
    assert payload["sub"] == "user-1"


def test_signing_key_from_jwt_missing_kid_raises():
    sig_jwk, private_pem = _rsa_jwk(kid="sig-kid")
    token = jwt.encode({"sub": "user-1"}, private_pem, algorithm="RS256")

    with pytest.raises(jwt.InvalidTokenError, match="missing kid"):
        signing_key_from_jwt({"keys": [sig_jwk]}, token)


def test_signing_key_from_jwt_unknown_kid_raises():
    sig_jwk, private_pem = _rsa_jwk(kid="sig-kid")
    token = jwt.encode(
        {"sub": "user-1"},
        private_pem,
        algorithm="RS256",
        headers={"kid": "other-kid"},
    )

    with pytest.raises(JwkSigningKeyNotFoundError, match="other-kid"):
        signing_key_from_jwt({"keys": [sig_jwk]}, token)
