"""
db — standard SQLAlchemy 2.x persistence layer (Postgres, Alembic-managed).

This package is the ONLY place that knows about SQLAlchemy, connection strings
and Neon/Postgres. The domain layer (claire_core.loop / state / agent / verifier)
never imports anything from here — it only ever sees the storage *ports*
(AttemptStore / ProfileStore / TeachingStateStore). The SQLAlchemy-backed
implementations of those ports live in `claire_core.persistence_sqlalchemy` and
take a session factory built here.
"""
from .base import (
    Base,
    SchemaOutOfDateError,
    check_schema_current,
    configure_engine,
    get_engine,
    get_sessionmaker,
    reset_engine,
    session_scope,
)

__all__ = [
    "Base",
    "SchemaOutOfDateError",
    "check_schema_current",
    "configure_engine",
    "get_engine",
    "get_sessionmaker",
    "reset_engine",
    "session_scope",
]
