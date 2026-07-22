"""
Proves the schema can be rebuilt from EMPTY by Alembic alone, and that the
startup guard fails loudly on an un-migrated database. Runs offline against a
throwaway SQLite file (same migration that targets Neon/Postgres).
"""
import os

import pytest
from sqlalchemy import create_engine, inspect

import db.base as db_base


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'schema.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    db_base.reset_engine()
    db_base.configure_engine(url)
    yield url
    db_base.reset_engine()


def test_alembic_rebuilds_from_empty(temp_db):
    from alembic import command

    cfg = db_base._alembic_config()

    # Empty DB → the startup guard must fail loudly (never silently create).
    with pytest.raises(db_base.SchemaOutOfDateError):
        db_base.check_schema_current()

    # Apply migrations from scratch.
    command.upgrade(cfg, "head")

    # All three tables now exist…
    engine = create_engine(temp_db)
    tables = set(inspect(engine).get_table_names())
    assert {"attempts", "student_profiles", "teaching_states"} <= tables

    # …and the guard is satisfied.
    db_base.check_schema_current()


def test_downgrade_removes_tables(temp_db):
    from alembic import command

    cfg = db_base._alembic_config()
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    engine = create_engine(temp_db)
    tables = set(inspect(engine).get_table_names())
    assert "attempts" not in tables
    assert "teaching_states" not in tables
