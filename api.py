"""
Claire API Backend - FastAPI version with SQLite rate limiting.

This replaces the Streamlit frontend with a proper API that can be deployed.
"""

import sqlite3
import logging
from datetime import date, datetime
from contextlib import contextmanager, asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel

from claire_agent_old import ClaireAgent
from api_auth import verify_jwt, get_optional_auth

# ============================================================
# Configuration
# ============================================================

DAILY_LIMIT = 20  # Free tier: 20 requests per day per user
DB_PATH = Path(__file__).parent / "usage.db"

# ============================================================
# Logging Setup
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# Database Setup
# ============================================================

def init_db():
    """Initialize SQLite database with usage table."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(user_id, date)
            )
        """)
        # Index for faster lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_date ON usage(user_id, date)
        """)
        conn.commit()
    logger.info(f"Database initialized at {DB_PATH}")


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ============================================================
# Rate Limiting Logic
# ============================================================

def get_user_id(request: Request) -> str:
    """
    Extract user identifier from request.
    Priority: X-User-ID header > X-Forwarded-For > client IP
    """
    # Check for custom user ID (from frontend UUID)
    user_id = request.headers.get("X-User-ID")
    if user_id:
        return f"uuid:{user_id}"

    # Check for forwarded IP (behind proxy/CDN)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"

    # Fallback to direct client IP
    return f"ip:{request.client.host}"


def check_and_increment_usage(user_id: str) -> dict:
    """
    Check user's daily usage and increment if under limit.
    Returns: {"allowed": bool, "used": int, "limit": int}
    """
    today = str(date.today())
    now = datetime.now().isoformat()

    with get_db() as conn:
        # Get current usage
        row = conn.execute(
            "SELECT count FROM usage WHERE user_id = ? AND date = ?",
            (user_id, today)
        ).fetchone()

        current_count = row["count"] if row else 0

        if current_count >= DAILY_LIMIT:
            return {"allowed": False, "used": current_count, "limit": DAILY_LIMIT}

        # Increment usage (upsert)
        conn.execute("""
            INSERT INTO usage (user_id, date, count, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                count = count + 1,
                updated_at = ?
        """, (user_id, today, now, now, now))
        conn.commit()

        return {"allowed": True, "used": current_count + 1, "limit": DAILY_LIMIT}


# ============================================================
# FastAPI App
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    # Startup
    init_db()
    logger.info("Claire API started")
    yield
    # Shutdown
    logger.info("Claire API stopped")


app = FastAPI(
    title="Claire API",
    description="Making Calculus Clear - AI Tutoring API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Request/Response Models
# ============================================================

class ChatRequest(BaseModel):
    message: str
    level: str = "beginner"  # beginner, intermediate, advanced
    guided_mode: bool = True
    problem_id: Optional[str] = None  # For example-level memory


class ChatResponse(BaseModel):
    output: str
    intermediate_steps: list
    usage: dict  # {"used": 5, "limit": 20, "remaining": 15}


class UsageResponse(BaseModel):
    used: int
    limit: int
    remaining: int


# ============================================================
# API Endpoints
# ============================================================

# Global agent instance (stateless, config passed per request)
agent = ClaireAgent()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Claire API",
        "version": "1.0.0"
    }


@app.get("/usage", response_model=UsageResponse)
async def get_usage(request: Request):
    """Check current usage for this user."""
    user_id = get_user_id(request)
    today = str(date.today())

    with get_db() as conn:
        row = conn.execute(
            "SELECT count FROM usage WHERE user_id = ? AND date = ?",
            (user_id, today)
        ).fetchone()

        used = row["count"] if row else 0

    return {
        "used": used,
        "limit": DAILY_LIMIT,
        "remaining": max(0, DAILY_LIMIT - used)
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    """
    Main chat endpoint - process a calculus question.

    Supports example-level memory when:
    - User is authenticated (Bearer token)
    - problem_id is provided
    - Workspace context has similar past attempts
    """
    user_id_for_rate_limit = get_user_id(request)
    start_time = datetime.now()

    # Check rate limit
    usage_result = check_and_increment_usage(user_id_for_rate_limit)

    if not usage_result["allowed"]:
        logger.warning(f"Rate limited: {user_id_for_rate_limit}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Daily limit reached",
                "message": "今日免费额度已用完，明天再来！",
                "used": usage_result["used"],
                "limit": usage_result["limit"]
            }
        )

    # Load workspace context for EXAMPLE-LEVEL memory
    # PROTECTION: If any lookup fails, skip memory silently (don't break /chat)
    memory_context = ""
    auth_user_id = None

    try:
        auth_user_id, auth_client = await get_optional_auth(request)

        if auth_user_id and body.problem_id:
            from workspace_context import WorkspaceContextAPI
            from problem_loader import get_problem_by_id

            context = WorkspaceContextAPI.load(auth_user_id, auth_client)
            if context:
                problem = get_problem_by_id(context.course, body.problem_id)
                if problem:
                    problem_stem = problem.stem or ""
                    if len(problem_stem) > 150:
                        problem_stem = problem_stem[:150] + "..."

                    memory_context = context.build_example_memory(
                        current_problem_id=body.problem_id,
                        current_topic=problem.topic,
                        current_problem_summary=problem_stem
                    )

                    if memory_context:
                        logger.info(
                            f"Memory context loaded for user={auth_user_id}, "
                            f"problem={body.problem_id}"
                        )
    except Exception as e:
        # Log but don't fail - /chat should still work without memory
        logger.warning(f"Memory context failed: {e}")

    # Inject memory into message
    enhanced_message = body.message
    if memory_context:
        enhanced_message = f"{memory_context}\n\n---\n\nStudent's current question:\n{body.message}"

    # Update agent settings
    agent.user_level = body.level
    agent.guided_mode = body.guided_mode

    # Process query
    try:
        result = agent.process_query(enhanced_message)

        # Log the request
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"user={user_id_for_rate_limit} | "
            f"auth_user={auth_user_id or 'anon'} | "
            f"question_len={len(body.message)} | "
            f"response_len={len(result.get('output', ''))} | "
            f"memory={'yes' if memory_context else 'no'} | "
            f"duration={duration:.2f}s | "
            f"usage={usage_result['used']}/{usage_result['limit']}"
        )

        return {
            "output": result.get("output", ""),
            "intermediate_steps": [
                {"tool": step.name, "result": step.content}
                if hasattr(step, "name") else str(step)
                for step in result.get("intermediate_steps", [])
            ],
            "usage": {
                "used": usage_result["used"],
                "limit": usage_result["limit"],
                "remaining": usage_result["limit"] - usage_result["used"]
            }
        }

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Processing failed", "message": str(e)}
        )


@app.get("/problems")
async def get_problems(course: str = "124"):
    """Get problems for a course."""
    import json
    from pathlib import Path

    problems_dir = Path(__file__).parent / "problems"
    all_problems = []

    course_prefix = f"math{course}_"

    for json_file in problems_dir.glob(f"{course_prefix}*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_problems.extend(data)
        except Exception as e:
            logger.warning(f"Failed to load {json_file}: {e}")

    # Sort by exam (newest first)
    all_problems.sort(key=lambda p: p.get("exam", ""), reverse=True)

    return {
        "course": course,
        "count": len(all_problems),
        "problems": all_problems
    }


@app.get("/problems/{problem_id}")
async def get_problem(problem_id: str):
    """Get a single problem by ID."""
    import json
    from pathlib import Path

    problems_dir = Path(__file__).parent / "problems"

    for json_file in problems_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    for problem in data:
                        if problem.get("id") == problem_id:
                            return problem
        except Exception as e:
            continue

    raise HTTPException(status_code=404, detail=f"Problem {problem_id} not found")


@app.get("/recommendations")
async def get_recommendations(request: Request, course: str = "124"):
    """
    Get personalized problem recommendations.

    Returns recommendations based on:
    - User's workspace context (if authenticated)
    - Student profile with topic mastery
    - Recent attempt history

    Security:
    - Uses JWT from Authorization header (RLS enforced)
    - Anonymous users get default recommendations
    """
    try:
        # Optional auth - works for both logged in and anonymous
        user_id, auth_client = await get_optional_auth(request)

        profile = None
        recent_attempts = None
        profile_summary = {}

        if user_id:
            from workspace_context import WorkspaceContextAPI

            context = WorkspaceContextAPI.load(user_id, auth_client)
            if context:
                profile = context.get_student_profile_v2()
                recent_attempts = context.recent_attempts

                profile_summary = {
                    "overall_accuracy": profile.overall_accuracy,
                    "total_attempts": profile.total_correct + profile.total_incorrect,
                    "priority_topics": profile.get_priority_topics()[:3],
                }

        # Generate recommendations
        from recommender_v2 import recommend_problems_for_api

        recommendations = recommend_problems_for_api(
            course=course,
            profile=profile,
            recent_attempts=recent_attempts,
            limit=5
        )

        logger.info(
            f"Recommendations: user={user_id or 'anon'}, "
            f"course={course}, count={len(recommendations)}"
        )

        return {
            "recommendations": recommendations,
            "profile_summary": profile_summary,
        }

    except Exception as e:
        logger.error(f"Recommendations failed: {e}", exc_info=True)
        # Return default recommendations on error
        from recommender_v2 import recommend_problems_for_api

        return {
            "recommendations": recommend_problems_for_api(course, None, None, 5),
            "profile_summary": {},
        }


@app.get("/stats")
async def get_stats():
    """Admin endpoint - get usage statistics."""
    today = str(date.today())

    with get_db() as conn:
        # Today's stats
        today_stats = conn.execute("""
            SELECT COUNT(DISTINCT user_id) as users, SUM(count) as requests
            FROM usage WHERE date = ?
        """, (today,)).fetchone()

        # Total stats
        total_stats = conn.execute("""
            SELECT COUNT(DISTINCT user_id) as users, SUM(count) as requests
            FROM usage
        """).fetchone()

    return {
        "today": {
            "unique_users": today_stats["users"] or 0,
            "total_requests": today_stats["requests"] or 0
        },
        "all_time": {
            "unique_users": total_stats["users"] or 0,
            "total_requests": total_stats["requests"] or 0
        }
    }


# ============================================================
# Mobile Upload API - QR code handwriting upload workflow
# ============================================================

from fastapi import UploadFile, File
from datetime import timezone, timedelta
import os

# Import mobile upload modules
from mobile_upload import (
    create_upload_session as _create_upload_session,
    validate_token,
    upload_image,
    get_session_status_lean,
    get_signed_urls,
    update_analysis_status,
    get_session_by_id,
)
from problem_loader import Problem, ProblemPart
from vision_analyzer import analyze_handwritten_solution, SolutionAnalysis


# --- Request/Response Models for Mobile API ---

class MobileSessionCreateRequest(BaseModel):
    user_id: str
    solve_session_id: str
    question_id: str
    course: str  # "124", "125", "126"
    display_text: Optional[str] = None


class MobileSessionResponse(BaseModel):
    session_id: str
    qr_url: str
    expires_at: str
    status: str


class MobileSessionStatusResponse(BaseModel):
    session_id: str
    status: str  # pending | uploaded | analyzing | analyzed | error | expired
    image_count: int
    analysis: Optional[dict] = None
    verification: Optional[dict] = None
    teaching_result: Optional[dict] = None
    error: Optional[str] = None


class MobileUploadResponse(BaseModel):
    success: bool
    image_url: Optional[str] = None
    image_count: int
    analysis: Optional[dict] = None
    verification: Optional[dict] = None
    teaching_result: Optional[dict] = None
    error: Optional[str] = None


class MobileResultResponse(BaseModel):
    session_id: str
    status: str  # pending | processing | completed | error | expired
    is_correct: Optional[bool] = None
    teaching_action: Optional[str] = None
    teaching_message: Optional[str] = None
    parts_summary: Optional[list] = None
    error: Optional[str] = None


# --- Helper Functions ---

def _get_frontend_base_url() -> str:
    """Get frontend base URL for QR codes."""
    return os.environ.get("FRONTEND_URL", "http://localhost:5173")


def _problem_dict_to_problem(problem_dict: dict) -> Problem:
    """Convert a problem dict (from JSON) to Problem dataclass."""
    parts = []
    for p in problem_dict.get("parts", []):
        parts.append(ProblemPart(
            label=p.get("label"),
            question_text=p.get("question_text", ""),
            final_answer=p.get("final_answer", ""),
            has_diagram=p.get("has_diagram", False),
            diagram_image=p.get("diagram_image"),
            diagram_image_url=p.get("diagram_image_url"),
            depends_on=p.get("depends_on"),
        ))

    return Problem(
        id=problem_dict.get("id", ""),
        course=problem_dict.get("course", ""),
        exam=problem_dict.get("exam", ""),
        problem_number=problem_dict.get("problem_number", 0),
        topic=problem_dict.get("topic", ""),
        concepts=problem_dict.get("concepts", []),
        points=problem_dict.get("points", 0),
        stem=problem_dict.get("stem"),
        parts=parts,
    )


def _analysis_to_dict(analysis: SolutionAnalysis) -> dict:
    """Convert SolutionAnalysis to serializable dict."""
    if not analysis:
        return None

    return {
        "overall_summary": analysis.overall_summary,
        "any_incorrect": analysis.any_incorrect,
        "any_uncertain": analysis.any_uncertain,
        "is_invalid_submission": analysis.is_invalid_submission,
        "invalid_submission_reason": analysis.invalid_submission_reason,
        "parts": [
            {
                "part_label": p.part_label,
                "student_final_answer": p.student_final_answer,
                "official_answer": p.official_answer,
                "is_correct": p.is_correct,
                "is_uncertain": p.is_uncertain,
                "feedback": p.feedback,
                "hint": p.hint,
                "error_type": p.error_type,
                "steps": p.steps,
            }
            for p in analysis.parts
        ]
    }


def _build_teaching_result(analysis: SolutionAnalysis, problem: Problem) -> dict:
    """Build teaching decision from analysis result."""
    if not analysis:
        return {
            "action": "error",
            "message": "Could not analyze your solution.",
            "reasoning": "Vision analysis failed",
        }

    # Handle invalid submission (wrong problem)
    if analysis.is_invalid_submission:
        return {
            "action": "give_feedback",
            "message": f"This doesn't appear to be a solution to the current problem. {analysis.invalid_submission_reason or ''}",
            "reasoning": "Submission doesn't match problem",
        }

    # Determine overall correctness
    all_correct = not analysis.any_incorrect and not analysis.any_uncertain
    any_uncertain = analysis.any_uncertain

    if all_correct:
        return {
            "action": "confirm_correct_and_stop",
            "message": f"Great work! {analysis.overall_summary}",
            "reasoning": "All parts verified correct",
        }
    elif any_uncertain:
        # Find uncertain parts
        uncertain_parts = [p for p in analysis.parts if p.is_uncertain]
        part_labels = ", ".join(p.part_label or str(i+1) for i, p in enumerate(uncertain_parts))
        return {
            "action": "ask_clarification",
            "message": f"I couldn't verify part(s) {part_labels} automatically. Could you walk me through your reasoning?",
            "reasoning": "Some parts uncertain, need clarification",
        }
    else:
        # Find incorrect parts
        incorrect_parts = [p for p in analysis.parts if not p.is_correct and not p.is_uncertain]
        if incorrect_parts:
            first_wrong = incorrect_parts[0]
            hint = first_wrong.hint or "Check your calculation."
            return {
                "action": "give_hint",
                "message": f"{first_wrong.feedback}\n\nHint: {hint}",
                "reasoning": f"Part {first_wrong.part_label or '1'} is incorrect",
            }
        else:
            return {
                "action": "give_feedback",
                "message": analysis.overall_summary,
                "reasoning": "General feedback",
            }


# --- Mobile Upload Endpoints ---

@app.post("/api/mobile/session", response_model=MobileSessionResponse)
async def create_mobile_session(body: MobileSessionCreateRequest):
    """
    Create a mobile upload session for QR code scanning.

    Returns session_id and qr_url that points to the mobile upload page.
    Session expires in 15 minutes.
    """
    logger.info(f"[mobile] Creating session for user={body.user_id}, question={body.question_id}")

    try:
        # Create the session using mobile_upload module
        session, raw_token = _create_upload_session(
            user_id=body.user_id,
            solve_session_id=body.solve_session_id,
            question_id=body.question_id,
            course=body.course,
            display_text=body.display_text,
            expires_minutes=15,
        )

        if not session:
            logger.error("[mobile] Failed to create session - no session returned")
            raise HTTPException(
                status_code=500,
                detail={"error": "session_create_failed", "message": "Could not create upload session"}
            )

        # Build QR URL pointing to mobile upload page
        frontend_base = _get_frontend_base_url()
        qr_url = f"{frontend_base}/mobile-upload/{session.id}?t={raw_token}"

        logger.info(f"[mobile] Session created: {session.id}, expires={session.expires_at}")

        return {
            "session_id": session.id,
            "qr_url": qr_url,
            "expires_at": session.expires_at.isoformat(),
            "status": session.status,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[mobile] Session create error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)}
        )


@app.get("/api/mobile/session/{session_id}", response_model=MobileSessionStatusResponse)
async def get_mobile_session_status(session_id: str):
    """
    Get current status of a mobile upload session.

    Status values:
    - pending: waiting for mobile to connect
    - paired: mobile connected, waiting for upload
    - uploaded: images uploaded, waiting for analysis
    - analyzing: vision + verification in progress
    - analyzed: analysis complete, results available
    - error: something went wrong
    - expired: session timed out
    """
    logger.debug(f"[mobile] Status request for session={session_id}")

    try:
        # Get session from database
        session = get_session_by_id(session_id)

        if not session:
            raise HTTPException(
                status_code=404,
                detail={"error": "session_not_found", "message": "Session not found"}
            )

        # Check expiry
        now = datetime.now(timezone.utc)
        if now > session.expires_at:
            return {
                "session_id": session_id,
                "status": "expired",
                "image_count": 0,
                "error": "Session expired",
            }

        # Get lean status with image count
        status_data = get_session_status_lean(session_id)

        # Map internal status to API status
        internal_status = status_data.get("status", "unknown")
        analysis_status = status_data.get("analysis_status", "pending")

        if internal_status in ["closed", "expired"]:
            api_status = "expired"
        elif analysis_status == "completed":
            api_status = "analyzed"
        elif analysis_status == "running":
            api_status = "analyzing"
        elif status_data.get("image_count", 0) > 0:
            api_status = "uploaded"
        elif internal_status == "paired":
            api_status = "paired"
        else:
            api_status = "pending"

        return {
            "session_id": session_id,
            "status": api_status,
            "image_count": status_data.get("image_count", 0),
            "analysis": status_data.get("analysis_result"),
            "verification": status_data.get("analysis_result", {}).get("verification") if status_data.get("analysis_result") else None,
            "teaching_result": status_data.get("analysis_result", {}).get("teaching_result") if status_data.get("analysis_result") else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[mobile] Status error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)}
        )


@app.post("/api/mobile/session/{session_id}/upload", response_model=MobileUploadResponse)
async def upload_mobile_image(
    session_id: str,
    file: UploadFile = File(...),
    t: Optional[str] = None,  # Token from query param
):
    """
    Upload a handwritten solution image from mobile.

    After successful upload:
    1. Image is stored in Supabase Storage
    2. Triggers Gemini Vision analysis
    3. Runs SymPy verifier
    4. Generates teaching decision

    Returns the analysis result and teaching decision.
    """
    logger.info(f"[mobile] Upload request for session={session_id}, file={file.filename}")

    try:
        # Validate token if provided
        if t:
            validated_session = validate_token(t)
            if not validated_session:
                raise HTTPException(
                    status_code=410,
                    detail={"error": "session_expired", "message": "Session expired or invalid token"}
                )
            if validated_session.id != session_id:
                raise HTTPException(
                    status_code=403,
                    detail={"error": "token_mismatch", "message": "Token does not match session"}
                )

        # Get session to check expiry and get question_id
        session = get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail={"error": "session_not_found", "message": "Session not found"}
            )

        # Check expiry
        now = datetime.now(timezone.utc)
        if now > session.expires_at:
            raise HTTPException(
                status_code=410,
                detail={"error": "session_expired", "message": "Session has expired"}
            )

        # Read file bytes
        file_bytes = await file.read()
        content_type = file.content_type or "image/jpeg"

        # Upload to storage
        storage_path, upload_error = upload_image(
            session_id=session_id,
            file_bytes=file_bytes,
            filename=file.filename or "upload.jpg",
            content_type=content_type,
        )

        if upload_error:
            logger.error(f"[mobile] Upload failed: {upload_error}")
            raise HTTPException(
                status_code=500,
                detail={"error": "upload_failed", "message": upload_error}
            )

        logger.info(f"[mobile] Image uploaded: {storage_path}")

        # Get current image count
        status_data = get_session_status_lean(session_id)
        image_count = status_data.get("image_count", 1)

        # Mark analysis as running
        update_analysis_status(session_id, "running")

        # Get signed URLs for all images
        image_urls = get_signed_urls(session_id)
        if not image_urls:
            logger.error("[mobile] No signed URLs available")
            update_analysis_status(session_id, "failed", {"error": "No images accessible"})
            raise HTTPException(
                status_code=500,
                detail={"error": "no_images", "message": "Could not access uploaded images"}
            )

        # Load problem for verification
        problem_dict = await get_problem(session.question_id)
        problem = _problem_dict_to_problem(problem_dict)

        logger.info(f"[mobile] Running analysis on {len(image_urls)} images for problem {problem.id}")

        # Run vision analysis + verification pipeline
        analysis, analysis_error = analyze_handwritten_solution(problem, image_urls)

        if analysis_error:
            logger.error(f"[mobile] Analysis failed: {analysis_error}")
            update_analysis_status(session_id, "failed", {"error": analysis_error})
            return {
                "success": True,  # Upload succeeded, analysis failed
                "image_url": image_urls[0] if image_urls else None,
                "image_count": image_count,
                "error": analysis_error,
            }

        # Build teaching decision
        teaching_result = _build_teaching_result(analysis, problem)

        # Convert to dict for storage
        analysis_dict = _analysis_to_dict(analysis)

        # Store complete result
        complete_result = {
            "analysis": analysis_dict,
            "verification": {
                "any_incorrect": analysis.any_incorrect,
                "any_uncertain": analysis.any_uncertain,
                "is_invalid": analysis.is_invalid_submission,
            },
            "teaching_result": teaching_result,
        }
        update_analysis_status(session_id, "completed", complete_result)

        logger.info(f"[mobile] Analysis complete: correct={not analysis.any_incorrect}, action={teaching_result['action']}")

        return {
            "success": True,
            "image_url": image_urls[0] if image_urls else None,
            "image_count": image_count,
            "analysis": analysis_dict,
            "verification": {
                "any_incorrect": analysis.any_incorrect,
                "any_uncertain": analysis.any_uncertain,
            },
            "teaching_result": teaching_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[mobile] Upload error: {e}", exc_info=True)
        update_analysis_status(session_id, "failed", {"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)}
        )


@app.get("/api/mobile/session/{session_id}/result", response_model=MobileResultResponse)
async def get_mobile_result(session_id: str):
    """
    Get final result for desktop polling.

    Returns a simplified response optimized for the desktop UI:
    - status: pending | processing | completed | error | expired
    - is_correct: true/false when analysis complete
    - teaching_action: what the student should do next
    - teaching_message: message to display
    - parts_summary: brief summary per part

    Desktop should poll this endpoint every 2-3 seconds while status is pending/processing.
    """
    logger.debug(f"[mobile] Result poll for session={session_id}")

    try:
        # Get session
        session = get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail={"error": "session_not_found", "message": "Session not found"}
            )

        # Check expiry
        now = datetime.now(timezone.utc)
        if now > session.expires_at:
            return {
                "session_id": session_id,
                "status": "expired",
                "error": "Session expired. Please generate a new QR code.",
            }

        # Get status with analysis result
        status_data = get_session_status_lean(session_id)
        analysis_status = status_data.get("analysis_status", "pending")
        analysis_result = status_data.get("analysis_result")

        # Map to simplified status
        if analysis_status == "completed" and analysis_result:
            # Analysis complete - return results
            teaching = analysis_result.get("teaching_result", {})
            analysis = analysis_result.get("analysis", {})

            is_correct = not analysis.get("any_incorrect", True)

            # Build parts summary
            parts_summary = []
            for part in analysis.get("parts", []):
                parts_summary.append({
                    "label": part.get("part_label", ""),
                    "correct": part.get("is_correct", False),
                    "feedback": part.get("feedback", ""),
                })

            return {
                "session_id": session_id,
                "status": "completed",
                "is_correct": is_correct,
                "teaching_action": teaching.get("action", "give_feedback"),
                "teaching_message": teaching.get("message", ""),
                "parts_summary": parts_summary,
            }

        elif analysis_status == "running":
            return {
                "session_id": session_id,
                "status": "processing",
            }

        elif analysis_status == "failed":
            return {
                "session_id": session_id,
                "status": "error",
                "error": analysis_result.get("error", "Analysis failed") if analysis_result else "Analysis failed",
            }

        else:
            # Still waiting
            image_count = status_data.get("image_count", 0)
            if image_count > 0:
                return {
                    "session_id": session_id,
                    "status": "processing",
                }
            else:
                return {
                    "session_id": session_id,
                    "status": "pending",
                }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[mobile] Result poll error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(e)}
        )


# ============================================================
# Payment & Quota API
# ============================================================

from quota import get_quota_status as _get_quota_status, is_pro_user
from stripe_checkout import create_checkout_session, get_customer_portal_url


class QuotaResponse(BaseModel):
    is_logged_in: bool
    remaining: int
    limit: int
    can_premium: bool
    limit_reached: bool
    is_pro: bool


class CheckoutRequest(BaseModel):
    user_id: str
    email: str


class CheckoutResponse(BaseModel):
    checkout_url: Optional[str] = None
    error: Optional[str] = None


@app.get("/api/quota", response_model=QuotaResponse)
async def get_quota(request: Request):
    """
    Get current user's quota status for upgrade flow.

    Returns:
        - remaining: queries left today (-1 for Pro)
        - limit: daily limit (-1 for Pro)
        - limit_reached: True if free quota exhausted
        - is_pro: True if user has active subscription
    """
    try:
        user_id, _ = await get_optional_auth(request)

        if user_id:
            # Check if Pro user (via Supabase)
            # Note: is_pro_user() uses session state which isn't available in API
            # So we check directly via Supabase
            from supabase import create_client
            import os

            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY")

            is_pro = False
            if supabase_url and supabase_key:
                try:
                    client = create_client(supabase_url, supabase_key)
                    resp = client.table("payments").select("status").eq("user_id", user_id).eq("status", "active").limit(1).execute()
                    is_pro = bool(resp.data)
                except Exception as e:
                    logger.warning(f"Pro check failed: {e}")

            if is_pro:
                return {
                    "is_logged_in": True,
                    "remaining": -1,
                    "limit": -1,
                    "can_premium": True,
                    "limit_reached": False,
                    "is_pro": True,
                }

            # Check daily usage from local DB
            today = str(date.today())
            with get_db() as conn:
                row = conn.execute(
                    "SELECT count FROM usage WHERE user_id = ? AND date = ?",
                    (f"uuid:{user_id}", today)
                ).fetchone()
                used = row["count"] if row else 0

            remaining = max(0, DAILY_LIMIT - used)
            return {
                "is_logged_in": True,
                "remaining": remaining,
                "limit": DAILY_LIMIT,
                "can_premium": remaining > 0,
                "limit_reached": remaining <= 0,
                "is_pro": False,
            }
        else:
            # Anonymous user - use IP-based tracking
            user_id_for_rate = get_user_id(request)
            today = str(date.today())

            with get_db() as conn:
                row = conn.execute(
                    "SELECT count FROM usage WHERE user_id = ? AND date = ?",
                    (user_id_for_rate, today)
                ).fetchone()
                used = row["count"] if row else 0

            remaining = max(0, DAILY_LIMIT - used)
            return {
                "is_logged_in": False,
                "remaining": remaining,
                "limit": DAILY_LIMIT,
                "can_premium": remaining > 0,
                "limit_reached": remaining <= 0,
                "is_pro": False,
            }

    except Exception as e:
        logger.error(f"Quota check failed: {e}", exc_info=True)
        # Return safe defaults
        return {
            "is_logged_in": False,
            "remaining": DAILY_LIMIT,
            "limit": DAILY_LIMIT,
            "can_premium": True,
            "limit_reached": False,
            "is_pro": False,
        }


@app.post("/api/checkout", response_model=CheckoutResponse)
async def create_checkout(body: CheckoutRequest):
    """
    Create a Stripe checkout session for Pro upgrade.

    Returns:
        - checkout_url: URL to redirect user to Stripe
    """
    try:
        checkout_url = create_checkout_session(body.user_id, body.email)
        if checkout_url:
            return {"checkout_url": checkout_url}
        else:
            return {"error": "Could not create checkout session"}
    except Exception as e:
        logger.error(f"Checkout failed: {e}", exc_info=True)
        return {"error": str(e)}


@app.post("/api/portal")
async def get_portal(request: Request):
    """
    Get Stripe customer portal URL for subscription management.
    """
    try:
        user_id, _ = await get_optional_auth(request)
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Get customer ID from Supabase
        from supabase import create_client
        import os

        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Payment system not configured")

        client = create_client(supabase_url, supabase_key)
        resp = client.table("payments").select("stripe_customer_id").eq("user_id", user_id).limit(1).execute()

        if not resp.data:
            raise HTTPException(status_code=404, detail="No subscription found")

        customer_id = resp.data[0].get("stripe_customer_id")
        if not customer_id:
            raise HTTPException(status_code=404, detail="No customer ID found")

        portal_url = get_customer_portal_url(customer_id)
        if portal_url:
            return {"portal_url": portal_url}
        else:
            raise HTTPException(status_code=500, detail="Could not create portal session")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portal failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Dashboard APIs: Exam Countdown, Must-Know Sections, Roadmap State
# ============================================================


class ExamCountdownResponse(BaseModel):
    next_exam: Optional[str]  # "exam_1" | "exam_2" | "final" | null
    next_exam_display: str  # "Exam I" | "Exam II" | "Final"
    days_until: int
    course: str
    course_display: str  # "Math 126"


@app.get("/api/exam-countdown", response_model=ExamCountdownResponse)
async def get_exam_countdown(request: Request):
    """
    Get days until next exam for the current user.

    Uses profile_data.selections.examTargetDate to calculate days.
    Currently defaults to "exam_1" since we don't have specific exam dates yet.
    """
    try:
        user_id, auth_client = await get_optional_auth(request)

        default_response = {
            "next_exam": "exam_1",
            "next_exam_display": "Exam I",
            "days_until": 14,
            "course": "math126",
            "course_display": "Math 126",
        }

        if not user_id or not auth_client:
            return default_response

        from workspace_context import WorkspaceContextAPI

        context = WorkspaceContextAPI.load(user_id, auth_client)
        if not context or not context.profile_data:
            return default_response

        profile_data = context.profile_data
        selections = profile_data.get("selections", {})

        # Get course
        course = selections.get("course") or context.course or "math126"
        course_display = {
            "math124": "Math 124",
            "math125": "Math 125",
            "math126": "Math 126",
        }.get(course, "Math 126")

        # Get exam type and calculate days until exam
        exam_type = selections.get("exam_type") or "midterm_1"
        exam_date = selections.get("exam_date")
        days_until = 14  # default

        # Map exam_type to display name
        exam_display_map = {
            "midterm_1": "Midterm I",
            "midterm_2": "Midterm II",
            "final": "Final",
        }
        next_exam_display = exam_display_map.get(exam_type, "Midterm I")

        if exam_date:
            try:
                from datetime import date as date_class
                exam_d = date_class.fromisoformat(exam_date)
                days_until = max(0, (exam_d - date.today()).days)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse exam_date: {e}")
                days_until = 14

        return {
            "next_exam": exam_type,
            "next_exam_display": next_exam_display,
            "days_until": days_until,
            "course": course,
            "course_display": course_display,
        }

    except Exception as e:
        logger.error(f"Exam countdown failed: {e}", exc_info=True)
        return {
            "next_exam": "exam_1",
            "next_exam_display": "Exam I",
            "days_until": 14,
            "course": "math126",
            "course_display": "Math 126",
        }


class MustKnowSection(BaseModel):
    section_id: str
    display_name: str
    priority_score: float
    checked: bool  # True if user has correct attempts in this section


class MustKnowSectionsResponse(BaseModel):
    sections: list[MustKnowSection]
    exam: str


@app.get("/api/must-know-sections", response_model=MustKnowSectionsResponse)
async def get_must_know_sections(request: Request, exam: str = "exam_1"):
    """
    Get top 3 priority sections to study before the exam.

    Priority score = exam_weight_score * 0.5 + untouched_score * 0.5
    - exam_weight_score: frequent concepts / total concepts in section
    - untouched_score: 1.0 if no attempts, 0.0 otherwise
    """
    try:
        from taxonomy.math126 import SECTIONS, SUBTOPIC_METADATA

        user_id, auth_client = await get_optional_auth(request)

        # Get user's attempt history by section
        section_attempts = {}
        if user_id and auth_client:
            from workspace_context import WorkspaceContextAPI
            context = WorkspaceContextAPI.load(user_id, auth_client)
            if context:
                # Build mapping of which sections have attempts
                for attempt in context.recent_attempts:
                    topic = attempt.get("topic")
                    if topic:
                        # Find which section this topic belongs to
                        for section in SECTIONS:
                            if topic in section.get("concepts", []):
                                sid = section["id"]
                                if sid not in section_attempts:
                                    section_attempts[sid] = {"count": 0, "correct": 0}
                                section_attempts[sid]["count"] += 1
                                if attempt.get("is_correct"):
                                    section_attempts[sid]["correct"] += 1
                                break

        # Filter sections by exam
        exam_sections = [s for s in SECTIONS if s.get("covered_in_exam") == exam]

        # Calculate priority score for each section
        scored_sections = []
        for section in exam_sections:
            concepts = section.get("concepts", [])
            if not concepts:
                continue

            # exam_weight_score: ratio of frequent concepts
            frequent_count = sum(
                1 for c in concepts
                if SUBTOPIC_METADATA.get(c, {}).get("frequent", False)
            )
            exam_weight_score = frequent_count / len(concepts) if concepts else 0

            # untouched_score: 1.0 if no attempts
            sid = section["id"]
            has_attempts = sid in section_attempts and section_attempts[sid]["count"] > 0
            untouched_score = 0.0 if has_attempts else 1.0

            # Combined score
            priority_score = exam_weight_score * 0.5 + untouched_score * 0.5

            # checked = has at least one correct attempt
            checked = sid in section_attempts and section_attempts[sid]["correct"] > 0

            scored_sections.append({
                "section_id": sid,
                "display_name": section["display_name"],
                "priority_score": round(priority_score, 2),
                "checked": checked,
            })

        # Sort by priority score descending, take top 3
        scored_sections.sort(key=lambda x: x["priority_score"], reverse=True)
        top_sections = scored_sections[:3]

        return {
            "sections": top_sections,
            "exam": exam,
        }

    except Exception as e:
        logger.error(f"Must-know sections failed: {e}", exc_info=True)
        return {
            "sections": [],
            "exam": exam,
        }


class RoadmapSection(BaseModel):
    section_id: str
    display_name: str
    week: int
    order: int
    covered_in_exam: str
    status: str  # "completed" | "current" | "in_progress" | "untouched"
    is_weak: bool
    attempts_count: int
    correct_rate: Optional[float]
    concepts: list[str]  # canonical topic IDs for filtering problems


class RoadmapStateResponse(BaseModel):
    sections: list[RoadmapSection]
    current_section_id: Optional[str]


@app.get("/api/roadmap-state", response_model=RoadmapStateResponse)
async def get_roadmap_state(request: Request):
    """
    Get status for all sections in the roadmap.

    Status rules:
    - "current": recommended by the system (first untouched or weak section)
    - "completed": correct attempts >= concepts * 2
    - "in_progress": has attempts but not completed
    - "untouched": no attempts

    is_weak: correct_rate < 0.5 AND attempts >= 3
    """
    try:
        from taxonomy.math126 import SECTIONS

        user_id, auth_client = await get_optional_auth(request)

        # Get user's attempt stats by section
        section_stats = {}
        if user_id and auth_client:
            from workspace_context import WorkspaceContextAPI
            context = WorkspaceContextAPI.load(user_id, auth_client)
            if context:
                for attempt in context.recent_attempts:
                    topic = attempt.get("topic")
                    if topic:
                        for section in SECTIONS:
                            if topic in section.get("concepts", []):
                                sid = section["id"]
                                if sid not in section_stats:
                                    section_stats[sid] = {"attempts": 0, "correct": 0}
                                section_stats[sid]["attempts"] += 1
                                if attempt.get("is_correct"):
                                    section_stats[sid]["correct"] += 1
                                break

        # Build roadmap state
        roadmap = []
        current_section_id = None

        # Sort sections by week, order
        sorted_sections = sorted(SECTIONS, key=lambda s: (s["week"], s["order"]))

        for section in sorted_sections:
            sid = section["id"]
            concepts_count = len(section.get("concepts", []))
            stats = section_stats.get(sid, {"attempts": 0, "correct": 0})

            attempts_count = stats["attempts"]
            correct_count = stats["correct"]
            correct_rate = correct_count / attempts_count if attempts_count > 0 else None

            # Determine status
            completion_threshold = concepts_count * 2
            if attempts_count == 0:
                status = "untouched"
            elif correct_count >= completion_threshold:
                status = "completed"
            else:
                status = "in_progress"

            # is_weak: low accuracy with sufficient attempts
            is_weak = correct_rate is not None and correct_rate < 0.5 and attempts_count >= 3

            # First untouched or weak section becomes "current"
            if current_section_id is None and status in ["untouched", "in_progress"]:
                current_section_id = sid
                status = "current"

            roadmap.append({
                "section_id": sid,
                "display_name": section["display_name"],
                "week": section["week"],
                "order": section["order"],
                "covered_in_exam": section["covered_in_exam"],
                "status": status,
                "is_weak": is_weak,
                "attempts_count": attempts_count,
                "correct_rate": round(correct_rate, 2) if correct_rate is not None else None,
                "concepts": section.get("concepts", []),
            })

        return {
            "sections": roadmap,
            "current_section_id": current_section_id,
        }

    except Exception as e:
        logger.error(f"Roadmap state failed: {e}", exc_info=True)
        return {
            "sections": [],
            "current_section_id": None,
        }


# ============================================================
# Personalized Roadmap API
# ============================================================

from plan_mode_calculator import get_plan_mode_description, get_countdown_text
from roadmap_generator import generate_roadmap, generate_high_value_sections, CoverageStrategy
from remediation_engine import get_remediation_items


def build_diagnostic_result(topic_stats: dict) -> dict:
    """
    Build diagnostic_result dict from topic_stats.

    Rules:
    - accuracy >= 0.7 → "ok"
    - accuracy >= 0.4 → "unstable"
    - accuracy < 0.4 → "weak"
    - no attempts → "unknown"
    """
    result = {}
    for topic, stats in topic_stats.items():
        attempts = stats.get("attempts", 0)
        if attempts == 0:
            result[topic] = "unknown"
        else:
            accuracy = stats.get("accuracy", 0)
            if accuracy >= 0.7:
                result[topic] = "ok"
            elif accuracy >= 0.4:
                result[topic] = "unstable"
            else:
                result[topic] = "weak"
    return result


class StudentPreferencesRequest(BaseModel):
    exam_type: Optional[str] = None  # midterm_1, midterm_2, final
    exam_date: Optional[str] = None  # ISO date string (YYYY-MM-DD)
    prep_level: Optional[str] = None  # no_class_no_homework, some_class_some_homework, etc.
    target_goal: Optional[str] = None  # pass, good, mastery


class StudentPreferencesResponse(BaseModel):
    status: str
    message: str


@app.post("/api/student-preferences", response_model=StudentPreferencesResponse)
async def save_student_preferences(request: Request, body: StudentPreferencesRequest):
    """
    Save exam_date, prep_level, target_goal to user profile.

    Saves to profile_data.selections in the student_profiles table.
    Requires authentication.
    """
    user_id, auth_client = await get_optional_auth(request)

    if not user_id or not auth_client:
        raise HTTPException(
            status_code=401,
            detail={"error": "auth_required", "message": "Authentication required to save preferences"}
        )

    try:
        # Load current workspace
        from workspace_context import WorkspaceContextAPI

        context = WorkspaceContextAPI.load(user_id, auth_client)
        if not context:
            raise HTTPException(
                status_code=404,
                detail={"error": "no_workspace", "message": "No active workspace found"}
            )

        # Get current profile_data and update selections
        current_profile_data = context.profile_data or {}
        selections = current_profile_data.get("selections", {})

        # Update with new values (only if provided)
        if body.exam_type is not None:
            selections["exam_type"] = body.exam_type
        if body.exam_date is not None:
            selections["exam_date"] = body.exam_date
        if body.prep_level is not None:
            selections["prep_level"] = body.prep_level
        if body.target_goal is not None:
            selections["target_goal"] = body.target_goal

        current_profile_data["selections"] = selections

        # Update in Supabase
        auth_client.table("student_profiles").update({
            "profile_data": current_profile_data
        }).eq("workspace_id", context.workspace_id).execute()

        logger.info(f"[preferences] Saved for user={user_id}: {selections}")

        return {
            "status": "saved",
            "message": "Preferences saved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[preferences] Save failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "save_failed", "message": str(e)}
        )


class RoadmapBlockItem(BaseModel):
    type: str  # exam_problem, mini_lesson
    problem_id: Optional[str] = None
    title: str
    source: Optional[str] = None
    points: Optional[int] = None


class RoadmapBlock(BaseModel):
    id: str
    block_id: str
    title: str
    reason: str
    priority: int
    topics: list[str]
    concepts: list[str]
    problem_count: int
    items: list[RoadmapBlockItem]


class RoadmapResponse(BaseModel):
    plan_mode: str
    plan_mode_description: dict
    days_until_exam: Optional[int]
    countdown_text: Optional[str]
    target_goal: Optional[str]
    prep_level: Optional[str]
    roadmap_blocks: list[RoadmapBlock]
    current_block: Optional[str]
    fallback_to_legacy: bool = False


@app.get("/api/roadmap")
async def get_roadmap(
    request: Request,
    course: str = "126",
    exam_date: Optional[str] = None,  # Fallback from frontend localStorage
    prep_level: Optional[str] = None,
    target_goal: Optional[str] = None,
):
    """
    Get personalized roadmap based on three-layer decision model.

    Layer 1: days_until_exam → coverage strategy
    Layer 2: prep_level → depth
    Layer 3: diagnostic_result → priority/depth adjustment

    Reads from profile first, then query params as fallback.
    Anonymous users can pass localStorage values via query params.

    Returns:
        RoadmapResponse with blocks ordered by priority
    """
    from problem_loader import load_problems

    # Dynamic taxonomy loading based on course
    def get_course_taxonomy(course_code):
        """Load SECTIONS and SUBTOPICS for the given course."""
        if course_code == "124":
            from taxonomy.math124 import SECTIONS, SUBTOPICS
            return SECTIONS, SUBTOPICS
        elif course_code == "125":
            from taxonomy.math125 import SECTIONS, SUBTOPICS
            return SECTIONS, SUBTOPICS
        else:  # Default to 126
            from taxonomy.math126 import SECTIONS, SUBTOPICS
            return SECTIONS, SUBTOPICS

    SECTIONS, SUBTOPICS = get_course_taxonomy(course)
    logger.info(f"[/api/roadmap] course={course}, SECTIONS count={len(SECTIONS)}, SUBTOPICS count={len(SUBTOPICS)}")

    try:
        user_id, auth_client = await get_optional_auth(request)

        # Try to get from profile first
        profile_exam_date = None
        profile_prep_level = None
        profile_target_goal = None
        diagnostic_result = {}
        context = None

        if user_id and auth_client:
            from workspace_context import WorkspaceContextAPI

            context = WorkspaceContextAPI.load(user_id, auth_client)
            if context:
                selections = context.profile_data.get("selections", {})
                profile_exam_date = selections.get("exam_date")
                profile_prep_level = selections.get("prep_level")
                profile_target_goal = selections.get("target_goal")

                # Build diagnostic_result from topic_stats
                topic_stats = context.get_topic_stats()
                diagnostic_result = build_diagnostic_result(topic_stats)

        # Use profile values, fallback to query params
        final_exam_date = profile_exam_date or exam_date
        final_prep_level = profile_prep_level or prep_level or "some_class_some_homework"  # Default
        final_target_goal = profile_target_goal or target_goal

        # Calculate days until exam (default to 14 if not set)
        days_until_exam = 14  # Default
        if final_exam_date:
            try:
                from datetime import date as date_class
                exam_d = date_class.fromisoformat(final_exam_date)
                days_until_exam = max(1, (exam_d - date.today()).days)  # At least 1 day
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse exam_date: {e}")

        # Generate roadmap using three-layer model
        roadmap_result = generate_roadmap(
            days_until_exam=days_until_exam,
            prep_level=final_prep_level,
            diagnostic_result=diagnostic_result,
            course=course,
        )

        # Generate high-value sections (分数杠杆，不是学习顺序)
        # 使用expected_loss算法，基于真题频率和分值
        high_value_result = generate_high_value_sections(
            days_until_exam=days_until_exam,
            diagnostic_result=diagnostic_result,
            course=course,
            num_recent_exams=5,
        )
        high_value_sections = high_value_result.get("high_value_topics", [])

        roadmap_items = roadmap_result.get("roadmap_items", [])
        coverage_strategy = roadmap_result.get("coverage_strategy", "full_personalized")

        # Build concept -> section mapping (using dynamically loaded SECTIONS)
        concept_to_section = {}
        for section in SECTIONS:
            for concept in section.get('concepts', []):
                concept_to_section[concept] = section

        # Build topic -> sections mapping
        topic_to_sections = {}
        for topic, concepts in SUBTOPICS.items():
            for concept in concepts:
                if concept in concept_to_section:
                    section = concept_to_section[concept]
                    if topic not in topic_to_sections:
                        topic_to_sections[topic] = []
                    if section not in topic_to_sections[topic]:
                        topic_to_sections[topic].append(section)

        # Build sections in roadmap order
        sections = []
        seen_section_ids = set()
        current_section_id = None

        for item in roadmap_items:
            topic_key = item["topic_key"]
            topic_sections = topic_to_sections.get(topic_key, [])

            for section in topic_sections:
                sid = section["id"]
                if sid in seen_section_ids:
                    continue
                seen_section_ids.add(sid)

                # Determine status based on priority
                if current_section_id is None:
                    status = "current"
                    current_section_id = sid
                else:
                    status = "untouched"

                sections.append({
                    "section_id": sid,
                    "display_name": section["display_name"],
                    "week": section.get("week", 1),
                    "order": len(sections),
                    "covered_in_exam": section.get("covered_in_exam", "exam_1"),
                    "status": status,
                    "is_weak": "diagnostic_weak" in item.get("reason_tags", []),
                    "attempts_count": 0,
                    "correct_rate": None,
                    "concepts": section.get("concepts", []),
                })

        # Also build roadmap_blocks for backwards compatibility
        all_problems = load_problems(course)
        roadmap_blocks = []
        current_block = None

        for item in roadmap_items:
            topic_key = item["topic_key"]
            subtopics = SUBTOPICS.get(topic_key, [])
            topic_problems = [p for p in all_problems if getattr(p, 'topic', None) == topic_key]

            sorted_problems = sorted(
                topic_problems,
                key=lambda p: (
                    0 if getattr(p, 'difficulty', '') == 'medium' else 1,
                    -(getattr(p, 'points', 0) or 0)
                )
            )[:3]

            items = []
            for p in sorted_problems:
                items.append({
                    "type": "exam_problem",
                    "problem_id": p.id,
                    "title": (p.stem or p.id)[:60],
                    "source": getattr(p, 'source', None),
                    "points": getattr(p, 'points', None),
                })

            reason_tags = item.get("reason_tags", [])
            if "diagnostic_weak" in reason_tags:
                reason = "Focus area based on your practice history"
            elif "diagnostic_unstable" in reason_tags:
                reason = "Needs more practice to solidify"
            elif "core_topic" in reason_tags:
                reason = "High-value exam topic"
            elif "prerequisite" in reason_tags:
                reason = "Foundation for other topics"
            else:
                reason = "Recommended study area"

            block = {
                "id": f"block_{topic_key}",
                "block_id": topic_key,
                "title": item["display_name"],
                "reason": reason,
                "priority": item["priority"],
                "topics": [topic_key],
                "concepts": subtopics,
                "problem_count": len(topic_problems),
                "items": items,
                "depth": item.get("depth", "quick_review"),
                "estimated_time_minutes": item.get("estimated_time_minutes", 20),
            }
            roadmap_blocks.append(block)

            # Set first block as current
            if current_block is None:
                current_block = block["id"]

        # Build countdown text
        countdown_text = get_countdown_text(days_until_exam)

        # Map coverage_strategy to plan_mode for backwards compatibility
        strategy_to_mode = {
            "core_cram": "cram",
            "crash_course": "crash_course",
            "compressed_full": "targeted_review",
            "full_personalized": "sweep",
        }
        plan_mode_str = strategy_to_mode.get(coverage_strategy, "sweep")

        # Build plan_mode_description
        plan_mode_description = {
            "cram": {"title": "Core Topics Cram", "description": "Focus on high-impact topics", "icon": "🔥", "urgency": "critical"},
            "crash_course": {"title": "Crash Course", "description": "Cover essentials quickly", "icon": "⚡", "urgency": "high"},
            "targeted_review": {"title": "Targeted Review", "description": "Strategic topic coverage", "icon": "🎯", "urgency": "moderate"},
            "sweep": {"title": "Full Review", "description": "Comprehensive preparation", "icon": "📚", "urgency": "low"},
        }.get(plan_mode_str, {"title": "Study Plan", "description": "Personalized roadmap", "icon": "📖", "urgency": "moderate"})

        logger.info(
            f"[roadmap] Generated for course={course}, "
            f"strategy={coverage_strategy}, days={days_until_exam}, "
            f"prep={final_prep_level}, "
            f"blocks={len(roadmap_blocks)}"
        )

        # If no SECTIONS defined for this course, use fallback
        use_fallback = len(SECTIONS) == 0 or len(sections) == 0
        if use_fallback:
            logger.info(f"[roadmap] course={course} has no SECTIONS, using fallback_to_legacy")

        return {
            "plan_mode": plan_mode_str,
            "plan_mode_description": plan_mode_description,
            "coverage_strategy": coverage_strategy,
            "days_until_exam": days_until_exam,
            "countdown_text": countdown_text,
            "target_goal": final_target_goal,
            "prep_level": final_prep_level,
            # 正确的sections格式，按roadmap优先级排序（学习路径）
            "sections": sections,
            "current_section_id": current_section_id,
            # 高价值sections，用于HighValueCard（分数杠杆）
            "high_value_sections": high_value_sections,
            # 保留roadmap_blocks用于其他用途
            "roadmap_blocks": roadmap_blocks,
            "current_block": current_section_id,  # Use section_id for consistency
            "fallback_to_legacy": use_fallback,
        }

    except Exception as e:
        logger.error(f"[roadmap] Generation failed: {e}", exc_info=True)
        # Return safe fallback
        return {
            "plan_mode": "sweep",
            "plan_mode_description": {"title": "Study Plan", "description": "Review all topics", "icon": "📚", "urgency": "low"},
            "coverage_strategy": "full_personalized",
            "days_until_exam": None,
            "countdown_text": None,
            "target_goal": None,
            "prep_level": None,
            "sections": [],
            "current_section_id": None,
            "high_value_sections": [],
            "roadmap_blocks": [],
            "current_block": None,
            "fallback_to_legacy": True,
        }


class RemediationRequest(BaseModel):
    problem_id: str
    detected_gap: Optional[str] = None
    prerequisite_concepts: Optional[list[str]] = None
    error_type: Optional[str] = None


class RemediationItem(BaseModel):
    type: str  # mini_lesson, basic_problem, retry
    problem_id: Optional[str] = None
    title: Optional[str] = None
    subtopic: Optional[str] = None
    content: Optional[str] = None
    display_name: Optional[str] = None
    source: Optional[str] = None
    reason: Optional[str] = None


class RemediationResponse(BaseModel):
    has_remediation: bool
    title: Optional[str] = None
    gap_description: Optional[str] = None
    items: list[RemediationItem] = []


@app.post("/api/remediation", response_model=RemediationResponse)
async def get_remediation(request: Request, body: RemediationRequest):
    """
    Get remediation items for a problem.

    V1: Only returns remediation if gap already detected externally.
    Returns has_remediation=false if no gap provided.
    """
    try:
        # Determine course from problem_id or default
        course = "126"  # TODO: extract from problem_id format

        result = get_remediation_items(
            body.detected_gap,
            body.prerequisite_concepts,
            body.problem_id,
            course,
        )

        return result

    except Exception as e:
        logger.error(f"[remediation] Failed: {e}", exc_info=True)
        return {
            "has_remediation": False,
            "items": [],
        }


# ============================================================
# Run with: uvicorn api:app --reload
# ============================================================
