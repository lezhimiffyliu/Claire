"""
app.persistence.base — engine / session factory + Alembic schema-currency guard.

Connection is driven entirely by the ``DATABASE_URL`` env var so that Neon is a
deploy-time swap, local Postgres is the dev default, and tests can inject an
in-memory SQLite engine — all without touching the domain layer.

Schema is owned by Alembic. ``check_schema_current()`` fails LOUDLY when the
database is behind head (or was never migrated). We never silently CREATE tables
in production and we never silently reset teaching state on a schema mismatch.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()

# Project root that holds alembic.ini / alembic/ (…/app/persistence/base.py -> …/)
_REPO_ROOT = Path(__file__).resolve().parents[2]

# Local dev default. Overridden in prod by DATABASE_URL (Neon), and by tests.
_DEFAULT_URL = "postgresql+psycopg2://localhost:5432/claire"

_engine: Optional[Engine] = None
_Session: Optional[sessionmaker] = None


class SchemaOutOfDateError(RuntimeError):
    """Raised when the DB schema revision does not match the Alembic head.

    We surface this instead of auto-creating tables so a misconfigured or
    un-migrated database can never silently drop teaching progression.
    """


def get_database_url() -> str:
    """Resolve the connection string (env first, local Postgres fallback)."""
    return os.getenv("DATABASE_URL", _DEFAULT_URL)


def _make_engine(url: str) -> Engine:
    # ``future=True`` keeps us on 2.x semantics. SQLite (tests) needs the
    # check_same_thread escape hatch when a single connection is shared.
    kwargs: dict = {"future": True, "pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs.pop("pool_pre_ping", None)
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def configure_engine(url: Optional[str] = None, *, engine: Optional[Engine] = None) -> Engine:
    """(Re)configure the process-wide engine + session factory.

    Tests call this with an in-memory SQLite engine; production leaves it to
    lazy initialization from DATABASE_URL.
    """
    global _engine, _Session
    if engine is None:
        engine = _make_engine(url or get_database_url())
    _engine = engine
    _Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return _engine


def reset_engine() -> None:
    """Drop the cached engine/session factory (used between test modules)."""
    global _engine, _Session
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _Session = None


def get_engine() -> Engine:
    if _engine is None:
        configure_engine()
    assert _engine is not None
    return _engine


def get_sessionmaker() -> sessionmaker:
    if _Session is None:
        configure_engine()
    assert _Session is not None
    return _Session


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional scope: commit on success, roll back on error, always close."""
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# --------------------------------------------------------------------------- #
# Alembic schema-currency guard
# --------------------------------------------------------------------------- #
def _alembic_config():
    from alembic.config import Config

    cfg = Config(str(_REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_REPO_ROOT / "alembic"))
    # Keep Alembic on the same URL as the app (env may override alembic.ini).
    cfg.set_main_option("sqlalchemy.url", get_database_url())
    return cfg


def check_schema_current(engine: Optional[Engine] = None) -> None:
    """Raise SchemaOutOfDateError unless the DB is at the Alembic head revision.

    Called at app startup so a stale/un-migrated database fails fast instead of
    corrupting or discarding teaching state.
    """
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    engine = engine or get_engine()
    script = ScriptDirectory.from_config(_alembic_config())
    heads = set(script.get_heads())

    with engine.connect() as conn:
        current = set(MigrationContext.configure(conn).get_current_heads())

    if current != heads:
        raise SchemaOutOfDateError(
            "Database schema is not at the Alembic head. "
            f"db={sorted(current) or ['<empty>']} head={sorted(heads)}. "
            "Run `alembic upgrade head` before starting the app."
        )
