"""
clerk_auth — Clerk JWT verification for FastAPI.

Identity comes ONLY from a cryptographically verified Clerk session token:

  * signature verified against Clerk's JWKS (RS256),
  * issuer checked against CLERK_JWT_ISSUER,
  * audience checked when CLERK_AUDIENCE is set,
  * expiry / issued-at enforced.

The verified ``sub`` claim is the user id. We NEVER read identity from an
``X-User-ID`` header or a request-body ``user_id`` field, so a client cannot
impersonate another user. An absent or invalid token means "anonymous" — the
caller decides what anonymous is allowed to do (here: graded but not persisted).

Configuration (env)
-------------------
    CLERK_JWT_ISSUER   e.g. https://your-app.clerk.accounts.dev   (required to auth)
    CLERK_JWKS_URL     defaults to <issuer>/.well-known/jwks.json
    CLERK_AUDIENCE     optional; when set, the aud claim is verified

Until real keys are configured, verification fails closed and every request is
treated as anonymous — the app still runs, just without persistence for anon.
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Optional

import jwt
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


class ClerkAuthError(Exception):
    """Raised when a presented token cannot be verified."""


def _config() -> dict:
    """Read Clerk config fresh each call so tests can set env at runtime."""
    issuer = os.getenv("CLERK_JWT_ISSUER") or os.getenv("CLERK_ISSUER")
    jwks_url = os.getenv("CLERK_JWKS_URL")
    if not jwks_url and issuer:
        jwks_url = issuer.rstrip("/") + "/.well-known/jwks.json"
    return {
        "issuer": issuer,
        "jwks_url": jwks_url,
        "audience": os.getenv("CLERK_AUDIENCE"),
    }


@lru_cache(maxsize=4)
def _jwks_client(jwks_url: str):
    # PyJWKClient caches keys and refreshes on unknown kid.
    return jwt.PyJWKClient(jwks_url)


def _signing_key_for_token(token: str):
    """Resolve the RSA signing key for this token from Clerk's JWKS.

    Isolated so tests can monkeypatch it with a locally generated public key
    instead of reaching the network.
    """
    cfg = _config()
    if not cfg["jwks_url"]:
        raise ClerkAuthError("Clerk not configured (no issuer / JWKS URL)")
    return _jwks_client(cfg["jwks_url"]).get_signing_key_from_jwt(token).key


def verify_clerk_token(token: str) -> str:
    """Verify a Clerk session JWT and return the user id (``sub``).

    Raises ClerkAuthError on any verification failure.
    """
    cfg = _config()
    if not cfg["issuer"]:
        raise ClerkAuthError("Clerk not configured (no issuer)")

    try:
        signing_key = _signing_key_for_token(token)
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=cfg["issuer"],
            audience=cfg["audience"] if cfg["audience"] else None,
            options={
                "require": ["exp", "iat", "sub"],
                "verify_aud": bool(cfg["audience"]),
            },
        )
    except ClerkAuthError:
        raise
    except Exception as exc:  # invalid signature / issuer / expired / malformed
        raise ClerkAuthError(f"token verification failed: {exc}") from exc

    sub = claims.get("sub")
    if not sub:
        raise ClerkAuthError("token has no subject")
    return str(sub)


def get_bearer_token(request: Request) -> Optional[str]:
    header = request.headers.get("Authorization")
    if not header or not header.startswith("Bearer "):
        return None
    token = header[len("Bearer ") :].strip()
    return token or None


def get_optional_identity(request: Request) -> Optional[str]:
    """Verified user id, or None for anonymous / unverifiable tokens.

    Never raises — a bad token is simply anonymous, so it can never be used to
    act as some other user.
    """
    token = get_bearer_token(request)
    if not token:
        return None
    try:
        return verify_clerk_token(token)
    except ClerkAuthError as exc:
        logger.info("[clerk] anonymous (token not verified): %s", exc)
        return None


def require_identity(request: Request) -> str:
    """Verified user id or 401. For endpoints that must be authenticated."""
    user_id = get_optional_identity(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id
