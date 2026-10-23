
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app import auth


@pytest.fixture
def signing_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private_key, private_key.public_key()


@pytest.fixture
def configured_auth(monkeypatch, signing_keys):
    private_key, public_key = signing_keys

    monkeypatch.setenv("KEYCLOAK_ISSUER", "https://issuer.example.test/realms/returnguard")
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "returnguard-api")
    monkeypatch.setenv(
        "KEYCLOAK_JWKS_URL",
        "https://issuer.example.test/realms/returnguard/protocol/openid-connect/certs",
    )
    monkeypatch.setenv("KEYCLOAK_CLIENT_ID", "returnguard-api")

    class FakeSigningKey:
        key = public_key

    class FakeJwksClient:
        def get_signing_key_from_jwt(self, token):
            return FakeSigningKey()

    monkeypatch.setattr(
        auth,
        "get_jwks_client",
        lambda jwks_url: FakeJwksClient(),
    )

    def make_token(
        roles=None,
        expires_in=timedelta(minutes=5),
        key=None,
    ):
        now = datetime.now(timezone.utc)

        claims = {
            "sub": "test-reviewer-123",
            "iss": "https://issuer.example.test/realms/returnguard",
            "aud": "returnguard-api",
            "iat": now,
            "exp": now + expires_in,
            "realm_access": {"roles": roles or []},
        }

        return jwt.encode(
            claims,
            key or private_key,
            algorithm="RS256",
        )

    return make_token


def test_missing_token_returns_401():
    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(credentials=None)

    assert exc.value.status_code == 401


def test_invalid_signature_returns_401(configured_auth, signing_keys):
    make_token = configured_auth
    another_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    token = make_token(key=another_private_key)

    from fastapi.security import HTTPAuthorizationCredentials

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(credentials=credentials)

    assert exc.value.status_code == 401


def test_expired_token_returns_401(configured_auth):
    from fastapi.security import HTTPAuthorizationCredentials

    token = configured_auth(expires_in=timedelta(seconds=-10))
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(HTTPException) as exc:
        auth.get_current_user(credentials=credentials)

    assert exc.value.status_code == 401


def test_valid_token_without_reviewer_role_returns_403(configured_auth):
    from fastapi.security import HTTPAuthorizationCredentials

    token = configured_auth(roles=["customer"])
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    claims = auth.get_current_user(credentials=credentials)

    with pytest.raises(HTTPException) as exc:
        auth.require_reviewer(claims=claims)

    assert exc.value.status_code == 403


def test_valid_reviewer_token_is_accepted(configured_auth):
    from fastapi.security import HTTPAuthorizationCredentials

    token = configured_auth(roles=["reviewer"])
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    claims = auth.get_current_user(credentials=credentials)
    reviewer_claims = auth.require_reviewer(claims=claims)

    assert reviewer_claims["sub"] == "test-reviewer-123"
    assert "reviewer" in reviewer_claims["realm_access"]["roles"]
