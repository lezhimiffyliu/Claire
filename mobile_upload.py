"""
Mobile Upload - QR code upload session management.

Security design:
- URL format: /upload?t=<token> - no sensitive data in URL
- Database stores token_hash (SHA-256), not raw token
- Token is one-time use, expires in 15 minutes
- Session bound to specific question_id
"""

from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import streamlit as st

_service_client = None


def _client():
    """Get authenticated Supabase client (with user session for RLS)."""
    try:
        from auth import get_authenticated_client
        return get_authenticated_client()
    except ImportError:
        return None


def _service_role_client():
    """
    Get Supabase client with service role key (bypasses RLS).
    Used for mobile operations where user isn't authenticated.
    """
    global _service_client
    if _service_client is None:
        try:
            from supabase import create_client
            import os

            url = None
            key = None

            # Try st.secrets first
            try:
                url = st.secrets.get("SUPABASE_URL")
                key = st.secrets.get("SUPABASE_SERVICE_KEY")
            except Exception:
                pass

            # Fallback to environment variables
            if not url:
                url = os.environ.get("SUPABASE_URL")
            if not key:
                key = os.environ.get("SUPABASE_SERVICE_KEY")

            if not url or not key:
                print("[mobile_upload] Missing SUPABASE_SERVICE_KEY for mobile operations")
                return None

            _service_client = create_client(url, key)
        except Exception as e:
            print(f"[mobile_upload] Service client error: {e}")
            return None
    return _service_client


@dataclass
class UploadSession:
    """Upload session data."""
    id: str
    token_hash: str
    user_id: str
    solve_session_id: str
    question_id: str
    course: str
    status: str  # waiting|paired|receiving_images|closed|expired
    problem_display_text: Optional[str]
    mobile_paired_at: Optional[datetime]
    created_at: datetime
    expires_at: datetime
    closed_at: Optional[datetime]
    # Analysis tracking
    analysis_status: str = "pending"  # pending|running|completed|failed
    analysis_result: Optional[dict] = None


@dataclass
class UploadedImage:
    """Uploaded image metadata."""
    id: str
    upload_session_id: str
    storage_path: str
    filename: str
    content_type: str
    size_bytes: int
    sequence_number: int
    uploaded_at: datetime


def generate_upload_token() -> tuple[str, str]:
    """
    Generate a secure upload token.

    Returns:
        (raw_token, token_hash) - raw_token goes in URL, hash goes in DB
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


def _hash_token(raw_token: str) -> str:
    """Hash a raw token for database lookup."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def create_upload_session(
    user_id: str,
    solve_session_id: str,
    question_id: str,
    course: str,
    display_text: Optional[str] = None,
    expires_minutes: int = 15,
) -> tuple[Optional[UploadSession], str]:
    """
    Create a new upload session.

    Closes any existing sessions for the same user/question.

    Args:
        user_id: Supabase user ID
        solve_session_id: Current solve session identifier
        question_id: Problem/question ID
        course: Course code (124, 125, 126)
        display_text: Problem text to show on mobile
        expires_minutes: Session expiry time (default 15 min)

    Returns:
        (UploadSession, raw_token) - raw_token for QR code URL
    """
    client = _client()
    if not client:
        return None, ""

    # Generate secure token
    raw_token, token_hash = generate_upload_token()

    # Calculate expiry
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expires_minutes)

    try:
        # Close any existing waiting/paired sessions for this user+question
        client.table("upload_sessions").update({
            "status": "closed",
            "closed_at": now.isoformat()
        }).eq("user_id", user_id).eq("question_id", question_id).in_(
            "status", ["waiting", "paired", "receiving_images"]
        ).execute()

        # Create new session
        result = client.table("upload_sessions").insert({
            "token_hash": token_hash,
            "user_id": user_id,
            "solve_session_id": solve_session_id,
            "question_id": question_id,
            "course": course,
            "status": "waiting",
            "problem_display_text": display_text,
            "expires_at": expires_at.isoformat(),
            "analysis_status": "pending",
        }).execute()

        if result.data and len(result.data) > 0:
            row = result.data[0]
            session = UploadSession(
                id=row["id"],
                token_hash=row["token_hash"],
                user_id=row["user_id"],
                solve_session_id=row["solve_session_id"],
                question_id=row["question_id"],
                course=row["course"],
                status=row["status"],
                problem_display_text=row.get("problem_display_text"),
                mobile_paired_at=None,
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                expires_at=datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")),
                closed_at=None,
                analysis_status=row.get("analysis_status", "pending"),
                analysis_result=row.get("analysis_result"),
            )
            return session, raw_token

    except Exception as e:
        print(f"[create_upload_session] Error: {e}")

    return None, ""


def validate_token(raw_token: str) -> Optional[UploadSession]:
    """
    Validate an upload token and return the session if valid.

    Checks:
    - Token exists in database
    - Session not expired
    - Session not closed

    Args:
        raw_token: Token from URL query parameter

    Returns:
        UploadSession if valid, None otherwise
    """
    # Use service role client - mobile users don't have auth session
    client = _service_role_client()
    if not client or not raw_token:
        return None

    token_hash = _hash_token(raw_token)

    try:
        result = client.table("upload_sessions").select("*").eq(
            "token_hash", token_hash
        ).execute()

        if not result.data or len(result.data) == 0:
            return None

        row = result.data[0]

        # Check expiry
        expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires_at:
            # Mark as expired
            client.table("upload_sessions").update({
                "status": "expired"
            }).eq("id", row["id"]).execute()
            return None

        # Check if closed
        if row["status"] in ["closed", "expired"]:
            return None

        # Parse mobile_paired_at if exists
        mobile_paired_at = None
        if row.get("mobile_paired_at"):
            mobile_paired_at = datetime.fromisoformat(
                row["mobile_paired_at"].replace("Z", "+00:00")
            )

        # Parse closed_at if exists
        closed_at = None
        if row.get("closed_at"):
            closed_at = datetime.fromisoformat(
                row["closed_at"].replace("Z", "+00:00")
            )

        return UploadSession(
            id=row["id"],
            token_hash=row["token_hash"],
            user_id=row["user_id"],
            solve_session_id=row["solve_session_id"],
            question_id=row["question_id"],
            course=row["course"],
            status=row["status"],
            problem_display_text=row.get("problem_display_text"),
            mobile_paired_at=mobile_paired_at,
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            expires_at=expires_at,
            closed_at=closed_at,
            analysis_status=row.get("analysis_status", "pending"),
            analysis_result=row.get("analysis_result"),
        )

    except Exception as e:
        print(f"[validate_token] Error: {e}")
        return None


def pair_mobile_session(session_id: str) -> bool:
    """
    Mark session as 'paired' on first mobile access.

    Args:
        session_id: UUID of the upload session

    Returns:
        True if successfully paired
    """
    # Use service role client - mobile users don't have auth session
    client = _service_role_client()
    if not client:
        return False

    try:
        now = datetime.now(timezone.utc)
        result = client.table("upload_sessions").update({
            "status": "paired",
            "mobile_paired_at": now.isoformat()
        }).eq("id", session_id).eq("status", "waiting").execute()

        return result.data and len(result.data) > 0

    except Exception as e:
        print(f"[pair_mobile_session] Error: {e}")
        return False


def upload_image(
    session_id: str,
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> tuple[Optional[str], Optional[str]]:
    """
    Upload image to Supabase Storage and create database record.

    Args:
        session_id: UUID of the upload session
        file_bytes: Raw image bytes
        filename: Original filename
        content_type: MIME type (image/png, image/jpeg, etc.)

    Returns:
        (storage_path, None) if successful, (None, error_message) otherwise
    """
    print("[DEBUG] entering upload_image")
    # Use service role client - mobile users don't have auth session
    client = _service_role_client()
    if not client:
        return None, "Service client not configured (missing SUPABASE_SERVICE_KEY)"

    try:
        # Get current image count for sequence number
        count_result = client.table("uploaded_images").select(
            "id", count="exact"
        ).eq("upload_session_id", session_id).execute()

        sequence = (count_result.count or 0) + 1

        # Generate storage path: uploads/{session_id}/{sequence}_{filename}
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        storage_path = f"{session_id}/{sequence}_{safe_filename}"

        # Upload to Supabase Storage
        client.storage.from_("uploads").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type}
        )

        # Create database record
        client.table("uploaded_images").insert({
            "upload_session_id": session_id,
            "storage_path": storage_path,
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(file_bytes),
            "sequence_number": sequence,
        }).execute()

        # Update session status to receiving_images
        client.table("upload_sessions").update({
            "status": "receiving_images"
        }).eq("id", session_id).execute()

        return storage_path, None

    except Exception as e:
        print(f"[upload_image] Error: {e}")
        return None, str(e)


def get_session_status(session_id: str) -> dict:
    """
    Get current status of an upload session.

    Args:
        session_id: UUID of the upload session

    Returns:
        Dict with status, image_count, and images list
    """
    # Use service role client to bypass RLS
    client = _service_role_client()
    if not client:
        return {"status": "error", "image_count": 0, "images": []}

    try:
        # Get session
        session_result = client.table("upload_sessions").select(
            "status"
        ).eq("id", session_id).execute()

        if not session_result.data:
            return {"status": "not_found", "image_count": 0, "images": []}

        status = session_result.data[0]["status"]

        # Get images
        images_result = client.table("uploaded_images").select(
            "id, storage_path, filename, sequence_number, uploaded_at"
        ).eq("upload_session_id", session_id).order("sequence_number").execute()

        images = []
        for row in images_result.data or []:
            images.append({
                "id": row["id"],
                "storage_path": row["storage_path"],
                "filename": row["filename"],
                "sequence": row["sequence_number"],
                "uploaded_at": row["uploaded_at"],
            })

        return {
            "status": status,
            "image_count": len(images),
            "images": images,
        }

    except Exception as e:
        print(f"[get_session_status] Error: {e}")
        return {"status": "error", "image_count": 0, "images": []}


def get_signed_urls(session_id: str, expires_in: int = 3600) -> list[str]:
    """
    Get signed URLs for all images in a session.

    Args:
        session_id: UUID of the upload session
        expires_in: URL expiry in seconds (default 1 hour)

    Returns:
        List of signed URLs for viewing images
    """
    # Use service role client to bypass RLS for retrieving uploaded images
    client = _service_role_client()
    if not client:
        print("[get_signed_urls] No service client available")
        return []

    try:
        # Get all images for session
        images_result = client.table("uploaded_images").select(
            "storage_path"
        ).eq("upload_session_id", session_id).order("sequence_number").execute()

        print(f"[get_signed_urls] Found {len(images_result.data or [])} images for session {session_id}")

        urls = []
        for row in images_result.data or []:
            storage_path = row["storage_path"]
            # Create signed URL
            signed = client.storage.from_("uploads").create_signed_url(
                path=storage_path,
                expires_in=expires_in
            )
            if signed and "signedURL" in signed:
                urls.append(signed["signedURL"])
            else:
                print(f"[get_signed_urls] Failed to create signed URL for {storage_path}: {signed}")

        return urls

    except Exception as e:
        print(f"[get_signed_urls] Error: {e}")
        return []


def close_session(session_id: str) -> bool:
    """
    Close an upload session.

    Args:
        session_id: UUID of the upload session

    Returns:
        True if successfully closed
    """
    client = _client()
    if not client:
        return False

    try:
        now = datetime.now(timezone.utc)
        result = client.table("upload_sessions").update({
            "status": "closed",
            "closed_at": now.isoformat()
        }).eq("id", session_id).execute()

        return result.data and len(result.data) > 0

    except Exception as e:
        print(f"[close_session] Error: {e}")
        return False


def get_analysis_status(session_id: str) -> dict:
    """
    Get ONLY the analysis status of a session (lean query for polling).

    Args:
        session_id: UUID of the upload session

    Returns:
        Dict with analysis_status, analysis_result (if completed), and image_count
    """
    client = _service_role_client()
    if not client:
        return {"analysis_status": "error"}

    try:
        # Single query: get analysis_status and analysis_result
        result = client.table("upload_sessions").select(
            "analysis_status, analysis_result"
        ).eq("id", session_id).execute()

        if not result.data:
            return {"analysis_status": "not_found"}

        row = result.data[0]
        return {
            "analysis_status": row.get("analysis_status", "pending"),
            "analysis_result": row.get("analysis_result"),
        }

    except Exception as e:
        print(f"[get_analysis_status] Error: {e}")
        return {"analysis_status": "error"}


def update_analysis_status(
    session_id: str,
    status: str,
    result: Optional[dict] = None
) -> bool:
    """
    Update the analysis status of a session.

    Args:
        session_id: UUID of the upload session
        status: New status (pending|running|completed|failed)
        result: Analysis result JSON (required when status=completed)

    Returns:
        True if successfully updated
    """
    client = _service_role_client()
    if not client:
        return False

    try:
        update_data = {"analysis_status": status}
        if result is not None:
            update_data["analysis_result"] = result

        client.table("upload_sessions").update(
            update_data
        ).eq("id", session_id).execute()

        return True

    except Exception as e:
        print(f"[update_analysis_status] Error: {e}")
        return False


def get_image_count(session_id: str) -> int:
    """
    Get the count of uploaded images for a session (lean query).

    Args:
        session_id: UUID of the upload session

    Returns:
        Number of uploaded images
    """
    client = _service_role_client()
    if not client:
        return 0

    try:
        result = client.table("uploaded_images").select(
            "id", count="exact"
        ).eq("upload_session_id", session_id).execute()

        return result.count or 0

    except Exception as e:
        print(f"[get_image_count] Error: {e}")
        return 0


def get_session_status_lean(session_id: str) -> dict:
    """
    Get session status and image count in a single efficient query.

    This is the primary polling function - combines status check with image count
    to minimize database round-trips.

    Args:
        session_id: UUID of the upload session

    Returns:
        Dict with status, analysis_status, and image_count
    """
    client = _service_role_client()
    if not client:
        return {"status": "error", "analysis_status": "error", "image_count": 0}

    try:
        # Single query for session status + analysis status
        session_result = client.table("upload_sessions").select(
            "status, analysis_status, analysis_result"
        ).eq("id", session_id).execute()

        if not session_result.data:
            return {"status": "not_found", "analysis_status": "not_found", "image_count": 0}

        row = session_result.data[0]

        # Get image count (separate query but efficient - count only)
        images_result = client.table("uploaded_images").select(
            "id", count="exact"
        ).eq("upload_session_id", session_id).execute()

        return {
            "status": row.get("status", "unknown"),
            "analysis_status": row.get("analysis_status", "pending"),
            "analysis_result": row.get("analysis_result"),
            "image_count": images_result.count or 0,
        }

    except Exception as e:
        print(f"[get_session_status_lean] Error: {e}")
        return {"status": "error", "analysis_status": "error", "image_count": 0}


def get_session_by_id(session_id: str) -> Optional[UploadSession]:
    """
    Get an upload session by ID (for desktop polling).

    Args:
        session_id: UUID of the upload session

    Returns:
        UploadSession if found, None otherwise
    """
    client = _client()
    if not client:
        return None

    try:
        result = client.table("upload_sessions").select("*").eq(
            "id", session_id
        ).execute()

        if not result.data or len(result.data) == 0:
            return None

        row = result.data[0]

        # Parse timestamps
        mobile_paired_at = None
        if row.get("mobile_paired_at"):
            mobile_paired_at = datetime.fromisoformat(
                row["mobile_paired_at"].replace("Z", "+00:00")
            )

        closed_at = None
        if row.get("closed_at"):
            closed_at = datetime.fromisoformat(
                row["closed_at"].replace("Z", "+00:00")
            )

        return UploadSession(
            id=row["id"],
            token_hash=row["token_hash"],
            user_id=row["user_id"],
            solve_session_id=row["solve_session_id"],
            question_id=row["question_id"],
            course=row["course"],
            status=row["status"],
            problem_display_text=row.get("problem_display_text"),
            mobile_paired_at=mobile_paired_at,
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            expires_at=datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")),
            closed_at=closed_at,
            analysis_status=row.get("analysis_status", "pending"),
            analysis_result=row.get("analysis_result"),
        )

    except Exception as e:
        print(f"[get_session_by_id] Error: {e}")
        return None
