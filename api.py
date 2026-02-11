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
from pydantic import BaseModel

from claire_agent import ClaireAgent

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
    """
    user_id = get_user_id(request)
    start_time = datetime.now()

    # Check rate limit
    usage_result = check_and_increment_usage(user_id)

    if not usage_result["allowed"]:
        logger.warning(f"Rate limited: {user_id}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Daily limit reached",
                "message": "今日免费额度已用完，明天再来！",
                "used": usage_result["used"],
                "limit": usage_result["limit"]
            }
        )

    # Update agent settings
    agent.user_level = body.level
    agent.guided_mode = body.guided_mode

    # Process query
    try:
        result = agent.process_query(body.message)

        # Log the request
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"user={user_id} | "
            f"question_len={len(body.message)} | "
            f"response_len={len(result.get('output', ''))} | "
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
# Run with: uvicorn api:app --reload
# ============================================================
