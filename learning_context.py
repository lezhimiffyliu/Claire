"""Learning context management with persistent resume support."""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
import streamlit as st
from functools import lru_cache

class CheckpointType(Enum):
    ONBOARDING = "onboarding"
    DIAGNOSTIC = "diagnostic"
    PRACTICE = "practice"

@lru_cache(maxsize=1)
def _get_supabase_client():
    """Singleton Supabase client with anon key."""
    from supabase import create_client
    import os
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

def _get_user_client():
    """Get client with user session (for RLS)."""
    from auth import get_user
    client = _get_supabase_client()
    if not client:
        return None
    user = get_user()
    if not user or not user.access_token:
        return None
    # Set auth header for RLS
    client.postgrest.auth(user.access_token)
    return client

@dataclass
class ResumeCheckpoint:
    type: CheckpointType
    diagnostic_index: Optional[int] = None
    diagnostic_question_ids: Optional[List[str]] = None
    problem_id: Optional[str] = None
    part_index: Optional[int] = None

    def to_dict(self):
        return {
            "type": self.type.value,
            "diagnostic_index": self.diagnostic_index,
            "diagnostic_question_ids": self.diagnostic_question_ids,
            "problem_id": self.problem_id,
            "part_index": self.part_index
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(
            type=CheckpointType(data.get("type", "onboarding")),
            diagnostic_index=data.get("diagnostic_index"),
            diagnostic_question_ids=data.get("diagnostic_question_ids"),
            problem_id=data.get("problem_id"),
            part_index=data.get("part_index")
        )

@dataclass
class WorkspaceContext:
    workspace_id: str
    user_id: str
    course: str
    checkpoint: Optional[ResumeCheckpoint]
    profile_data: dict
    diagnostic_completed: bool

    @classmethod
    def load(cls, user_id: str) -> Optional['WorkspaceContext']:
        """Load active workspace from Supabase (RLS enforced)."""
        client = _get_user_client()
        if not client:
            return None

        try:
            # Query active workspace with profile (RLS: user_id match enforced)
            result = client.table("workspaces").select(
                "id, course, student_profiles(profile_data, checkpoint, diagnostic_completed)"
            ).eq("user_id", user_id).eq("is_active", True).limit(1).execute()

            if not result.data:
                return None

            ws = result.data[0]
            profiles = ws.get("student_profiles", [])
            if not profiles:
                return None

            profile = profiles[0]
            checkpoint_data = profile.get("checkpoint")
            checkpoint = ResumeCheckpoint.from_dict(checkpoint_data)

            # Determine checkpoint type if missing
            if not checkpoint:
                diagnostic_completed = profile.get("diagnostic_completed", False)
                checkpoint = ResumeCheckpoint(
                    type=CheckpointType.PRACTICE if diagnostic_completed else CheckpointType.DIAGNOSTIC
                )

            return cls(
                workspace_id=ws["id"],
                user_id=user_id,
                course=ws["course"],
                checkpoint=checkpoint,
                profile_data=profile.get("profile_data") or {},
                diagnostic_completed=profile.get("diagnostic_completed", False)
            )
        except Exception as e:
            print(f"[learning_context] Load failed: {e}")
            return None

    def save_checkpoint(self, checkpoint: ResumeCheckpoint):
        """Save checkpoint only (lightweight, RLS enforced)."""
        client = _get_user_client()
        if not client:
            return

        try:
            client.table("student_profiles").update({
                "checkpoint": checkpoint.to_dict()
            }).eq("workspace_id", self.workspace_id).eq("user_id", self.user_id).execute()

            self.checkpoint = checkpoint
        except Exception as e:
            print(f"[learning_context] Save checkpoint failed: {e}")

    def save_profile(self, profile_data: dict, diagnostic_completed: bool = None):
        """Save profile data (after grading/diagnostic, RLS enforced)."""
        client = _get_user_client()
        if not client:
            return

        try:
            update_data = {"profile_data": profile_data}
            if diagnostic_completed is not None:
                update_data["diagnostic_completed"] = diagnostic_completed

            client.table("student_profiles").update(update_data).eq(
                "workspace_id", self.workspace_id
            ).eq("user_id", self.user_id).execute()

            self.profile_data = profile_data
            if diagnostic_completed is not None:
                self.diagnostic_completed = diagnostic_completed
        except Exception as e:
            print(f"[learning_context] Save profile failed: {e}")

    @classmethod
    def create(cls, user_id: str, course: str) -> Optional['WorkspaceContext']:
        """Create new workspace (RLS enforced)."""
        client = _get_user_client()
        if not client:
            return None

        try:
            # Deactivate old workspaces for this user+course
            client.table("workspaces").update({"is_active": False}).eq(
                "user_id", user_id
            ).eq("course", course).execute()

            # Create new workspace
            ws_result = client.table("workspaces").insert({
                "user_id": user_id,
                "course": course,
                "is_active": True
            }).execute()

            workspace_id = ws_result.data[0]["id"]

            # Create profile
            client.table("student_profiles").insert({
                "workspace_id": workspace_id,
                "user_id": user_id,
                "profile_data": {},
                "checkpoint": ResumeCheckpoint(type=CheckpointType.DIAGNOSTIC).to_dict(),
                "diagnostic_completed": False
            }).execute()

            return cls(
                workspace_id=workspace_id,
                user_id=user_id,
                course=course,
                checkpoint=ResumeCheckpoint(type=CheckpointType.DIAGNOSTIC),
                profile_data={},
                diagnostic_completed=False
            )
        except Exception as e:
            print(f"[learning_context] Create failed: {e}")
            return None

def get_context() -> Optional[WorkspaceContext]:
    """Get context from session cache."""
    return st.session_state.get("workspace_context")

def set_context(ctx: WorkspaceContext):
    """Set context in session cache."""
    st.session_state.workspace_context = ctx
