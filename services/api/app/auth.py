
import os
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError


bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_settings() -> tuple[str, str, str]:
    """Return the trusted Keycloak issuer, audience, and JWKS URL."""
    issuer = os.getenv("KEYCLOAK_ISSUER", "").rstrip("/")
    audience = os.getenv("KEYCLOAK_AUDIENCE", "")
    jwks_url = os.getenv("KEYCLOAK_JWKS_URL", "")

    if not issuer or not audience or not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )

    return issuer, audience, jwks_url


@lru_cache(maxsize=4)
def get_jwks_client(jwks_url: str) -> PyJWKClient:
    """Cache the trusted Keycloak JWKS client."""
    return PyJWKClient(jwks_url)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Verify the access token and return its trusted claims."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    issuer, audience, jwks_url = get_auth_settings()
    token = credentials.credentials

    try:
        signing_key = get_jwks_client(jwks_url).get_signing_key_from_jwt(token)

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            audience=audience,
            options={
                "require": ["exp", "iat", "iss", "sub", "aud"],
            },
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except Exception as exc:
        # Includes JWKS/network failures. Do not accept a token when
        # its signature cannot be verified.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify access token",
        ) from exc

    return claims


def require_reviewer(
    claims: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Require the reviewer role in the Keycloak access token."""
    realm_roles = claims.get("realm_access", {}).get("roles", [])
    client_roles = claims.get("resource_access", {}).get(
        os.getenv("KEYCLOAK_CLIENT_ID", ""), {}
    ).get("roles", [])

    if "reviewer" not in realm_roles and "reviewer" not in client_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer permission required",
        )

    return claims
