
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app import auth


ISSUER = "https://issuer.example.test/realms/returnguard"
AUDIENCE = "returnguard-api"
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"


@pytest.fixture
def api_auth_setup(monkeypatch):
    """Configure test issuer and keys without running Keycloak."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    monkeypatch.setenv("KEYCLOAK_ISSUER", ISSUER)
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("KEYCLOAK_JWKS_URL", JWKS_URL)
    monkeypatch.setenv("KEYCLOAK_CLIENT_ID", "returnguard-api")

    class FakeSigningKey:
        key = public_key

    class FakeJwksClient:
        def get_signing_key_from_jwt(self, token):
            return FakeSigningKey()

    # Mock only the key lookup. PyJWT still verifies signatures and claims.
    monkeypatch.setattr(
        auth,
        "get_jwks_client",
        lambda jwks_url: FakeJwksClient(),
    )

    def make_token(roles=None, expires_in=timedelta(minutes=5), key=None):
        now = datetime.now(timezone.utc)

        claims = {
            "sub": "api-test-reviewer",
            "iss": ISSUER,
            "aud": AUDIENCE,
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


def create_pending_case(client, case_id="api-auth-review-case"):
    response = client.post(
        "/returns/evaluate",
        json={
            "case_id": case_id,
            "order_id": f"order-{case_id}",
            "order_amount": "2500.00",
            "refund_amount": "500.00",
            "days_since_delivery": 3,
            "return_window_days": 30,
            "evidence_required": False,
            "evidence_available": True,
            "duplicate_request": False,
            "previous_returns_90d": 0,
            "delivery_status": "delivered",
            "evidence_consistent": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["outcome"] == "human_review"


def submit_review(client, case_id, token=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    return client.post(
        f"/returns/{case_id}/review",
        headers=headers,
        json={
            "decision": "approve",
            "reason": "Evidence verified in API authentication test.",
        },
    )


def test_review_without_token_returns_401(client, api_auth_setup):
    create_pending_case(client)

    response = submit_review(client, "api-auth-review-case")

    assert response.status_code == 401


def test_review_with_invalid_signature_returns_401(
    client, api_auth_setup
):
    create_pending_case(client)
    make_token = api_auth_setup

    attacker_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    token = make_token(key=attacker_key)

    response = submit_review(
        client,
        "api-auth-review-case",
        token,
    )

    assert response.status_code == 401


def test_review_with_expired_token_returns_401(
    client, api_auth_setup
):
    create_pending_case(client)
    token = api_auth_setup(
        roles=["reviewer"],
        expires_in=timedelta(seconds=-10),
    )

    response = submit_review(
        client,
        "api-auth-review-case",
        token,
    )

    assert response.status_code == 401


def test_review_without_reviewer_role_returns_403(
    client, api_auth_setup
):
    create_pending_case(client)
    token = api_auth_setup(roles=["customer"])

    response = submit_review(
        client,
        "api-auth-review-case",
        token,
    )

    assert response.status_code == 403


def test_valid_reviewer_token_can_submit_review(
    client, api_auth_setup
):
    create_pending_case(client)
    token = api_auth_setup(roles=["reviewer"])

    response = submit_review(
        client,
        "api-auth-review-case",
        token,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
