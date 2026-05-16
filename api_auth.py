# api_auth.py
"""
FastAPI JWT verification for Supabase Auth.
Uses anon key + user's JWT for RLS enforcement.

Security:
- NEVER use service_role key
- NEVER trust X-User-ID from frontend
- ALWAYS verify JWT with Supabase auth.get_user()
- ALWAYS use authenticated client for RLS queries
"""
from functools import lru_cache
from typing import Optional, Tuple
from fastapi import Request, HTTPException
import os


@lru_cache(maxsize=1)
def _get_anon_client():
    """Singleton Supabase client with anon key (for validation only)."""
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_KEY")  # anon key, NOT service_role

    if not url or not anon_key:
        return None

    return create_client(url, anon_key)


def get_authenticated_client_from_token(access_token: str):
    """
    Create authenticated Supabase client from JWT.
    This enables RLS based on auth.uid().

    Args:
        access_token: User's JWT access token

    Returns:
        Supabase client with auth set for RLS
    """
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_KEY")

    if not url or not anon_key:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    client = create_client(url, anon_key)
    # Set the user's JWT - this makes RLS work
    client.postgrest.auth(access_token)
    return client


async def verify_jwt(request: Request) -> Tuple[str, any]:
    """
    Extract and verify JWT from Authorization header.

    Args:
        request: FastAPI request object

    Returns:
        Tuple of (user_id, authenticated_client)

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )

    token = auth_header.replace("Bearer ", "")

    # Verify token by calling Supabase auth.get_user()
    # This validates the JWT and returns user info
    base_client = _get_anon_client()
    if not base_client:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    try:
        # auth.get_user(token) validates JWT and returns user
        user_response = base_client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = user_response.user.id

        # Create authenticated client for RLS queries
        auth_client = get_authenticated_client_from_token(token)

        return user_id, auth_client

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token verification failed: {str(e)}"
        )


async def get_optional_auth(request: Request) -> Tuple[Optional[str], any]:
    """
    Like verify_jwt but returns (None, anon_client) for anonymous users.
    Useful for endpoints that work both authenticated and anonymous.

    Args:
        request: FastAPI request object

    Returns:
        Tuple of (user_id or None, client)
        - If authenticated: (user_id, auth_client)
        - If anonymous: (None, anon_client)
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, _get_anon_client()

    try:
        return await verify_jwt(request)
    except HTTPException:
        # Token present but invalid - return anonymous
        return None, _get_anon_client()
