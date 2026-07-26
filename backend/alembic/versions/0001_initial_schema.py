"""initial tutoring schema: attempts, student_profiles, teaching_states

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-21

Creates the three tables that back the storage ports used by
claire_core.run_tutor_turn. JSON columns are JSONB on Postgres and plain JSON
elsewhere, so the same migration applies to Neon, local Postgres and SQLite.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# JSONB on Postgres, JSON otherwise.
JSONType = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "attempts",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("problem_id", sa.String(length=128), nullable=False),
        sa.Column(
            "attempt_session_id",
            sa.String(length=128),
            nullable=False,
            server_default="default",
        ),
        sa.Column("workspace_id", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=32), server_default="practice"),
        sa.Column("submitted_answer", sa.Text(), nullable=True),
        sa.Column("grade_status", sa.String(length=32), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("action", sa.String(length=48), nullable=True),
        sa.Column("hint_level", sa.String(length=32), nullable=True),
        sa.Column("misconception", sa.String(length=48), nullable=True),
        sa.Column("error_type", sa.String(length=32), nullable=True),
        sa.Column("used_hint", sa.Boolean(), server_default=sa.false()),
        sa.Column("topic", sa.String(length=128), nullable=True),
        sa.Column("concept", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_attempts_user_id", "attempts", ["user_id"])
    op.create_index("ix_attempts_problem_id", "attempts", ["problem_id"])
    op.create_index(
        "ix_attempts_attempt_session_id", "attempts", ["attempt_session_id"]
    )

    op.create_table(
        "student_profiles",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("course", sa.String(length=16), nullable=False, server_default="124"),
        sa.Column("profile_data", JSONType, nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "course", name="uq_profile_user_course"),
    )
    op.create_index("ix_student_profiles_user_id", "student_profiles", ["user_id"])

    op.create_table(
        "teaching_states",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("problem_id", sa.String(length=128), nullable=False),
        sa.Column(
            "attempt_session_id",
            sa.String(length=128),
            nullable=False,
            server_default="default",
        ),
        sa.Column("phase", sa.String(length=32), server_default="awaiting_attempt"),
        sa.Column("attempt_count", sa.Integer(), server_default="0"),
        sa.Column("hint_level", sa.String(length=32), server_default="none"),
        sa.Column("misconception", sa.String(length=48), nullable=True),
        sa.Column("explained_concepts", JSONType, nullable=True),
        sa.Column("hints_given", JSONType, nullable=True),
        sa.Column("last_action", sa.String(length=48), nullable=True),
        sa.Column("last_question", sa.Text(), nullable=True),
        sa.Column("used_hint", sa.Boolean(), server_default=sa.false()),
        sa.Column("state_data", JSONType, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id",
            "problem_id",
            "attempt_session_id",
            name="uq_teaching_user_problem_session",
        ),
    )
    op.create_index("ix_teaching_states_user_id", "teaching_states", ["user_id"])
    op.create_index("ix_teaching_states_problem_id", "teaching_states", ["problem_id"])
    op.create_index(
        "ix_teaching_states_attempt_session_id",
        "teaching_states",
        ["attempt_session_id"],
    )


def downgrade() -> None:
    op.drop_table("teaching_states")
    op.drop_table("student_profiles")
    op.drop_table("attempts")
