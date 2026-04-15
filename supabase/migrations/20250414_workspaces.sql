-- Migration: Add workspaces, student_profiles, attempt_history tables
-- Date: 2025-04-14
-- RLS Principle: Every table has user_id, policy = WHERE user_id = auth.uid()

-- =============================================================================
-- Table: workspaces
-- =============================================================================
CREATE TABLE IF NOT EXISTS workspaces (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    course        TEXT NOT NULL,  -- '124' | '125' | '126'
    name          TEXT NOT NULL DEFAULT 'My Workspace',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(user_id, course)
);

CREATE INDEX IF NOT EXISTS idx_workspaces_user_id ON workspaces(user_id);

-- =============================================================================
-- Table: student_profiles
-- =============================================================================
CREATE TABLE IF NOT EXISTS student_profiles (
    workspace_id  UUID PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    profile_data  JSONB NOT NULL DEFAULT '{}',
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_student_profiles_user_id ON student_profiles(user_id);

-- =============================================================================
-- Table: attempt_history
-- =============================================================================
CREATE TABLE IF NOT EXISTS attempt_history (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    workspace_id        UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    question_id         TEXT NOT NULL,
    source              TEXT NOT NULL,  -- 'diagnostic' | 'practice' | 'handwritten_upload'
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_correct          BOOLEAN,
    final_answer        TEXT,           -- student's submitted answer
    error_type          TEXT,           -- 'concept' | 'algebra' | 'logic' | 'careless' | 'uncertain'
    topic               TEXT,
    concept             TEXT,
    upload_session_id   UUID,           -- nullable, references upload_sessions
    analysis_summary    TEXT,           -- brief summary of vision analysis
    analysis_data       JSONB,          -- full analysis result
    uploaded_image_id   UUID            -- nullable, references uploaded_images
);

CREATE INDEX IF NOT EXISTS idx_attempt_history_user_id ON attempt_history(user_id);
CREATE INDEX IF NOT EXISTS idx_attempt_history_workspace_id ON attempt_history(workspace_id);
CREATE INDEX IF NOT EXISTS idx_attempt_history_question_id ON attempt_history(question_id);
CREATE INDEX IF NOT EXISTS idx_attempt_history_submitted_at ON attempt_history(submitted_at DESC);

-- =============================================================================
-- RLS Policies (Split: SELECT USING + INSERT WITH CHECK + UPDATE/DELETE USING)
-- =============================================================================

ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE attempt_history ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- workspaces
-- -----------------------------------------------------------------------------
CREATE POLICY workspaces_select ON workspaces
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY workspaces_insert ON workspaces
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY workspaces_update ON workspaces
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY workspaces_delete ON workspaces
    FOR DELETE USING (user_id = auth.uid());

-- -----------------------------------------------------------------------------
-- student_profiles
-- -----------------------------------------------------------------------------
CREATE POLICY student_profiles_select ON student_profiles
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY student_profiles_insert ON student_profiles
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY student_profiles_update ON student_profiles
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY student_profiles_delete ON student_profiles
    FOR DELETE USING (user_id = auth.uid());

-- -----------------------------------------------------------------------------
-- attempt_history
-- -----------------------------------------------------------------------------
CREATE POLICY attempt_history_select ON attempt_history
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY attempt_history_insert ON attempt_history
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY attempt_history_update ON attempt_history
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY attempt_history_delete ON attempt_history
    FOR DELETE USING (user_id = auth.uid());

-- =============================================================================
-- uploaded_images RLS (EXISTS写法，更严格)
-- 仅当 upload_session 属于当前用户时才可访问
-- =============================================================================
-- Note: Run this after upload_sessions and uploaded_images tables exist
--
-- ALTER TABLE uploaded_images ENABLE ROW LEVEL SECURITY;
--
-- CREATE POLICY uploaded_images_select ON uploaded_images
--     FOR SELECT USING (
--         EXISTS (
--             SELECT 1 FROM upload_sessions us
--             WHERE us.id = uploaded_images.upload_session_id
--               AND us.user_id = auth.uid()
--         )
--     );
--
-- CREATE POLICY uploaded_images_insert ON uploaded_images
--     FOR INSERT WITH CHECK (
--         EXISTS (
--             SELECT 1 FROM upload_sessions us
--             WHERE us.id = uploaded_images.upload_session_id
--               AND us.user_id = auth.uid()
--         )
--     );
--
-- CREATE POLICY uploaded_images_delete ON uploaded_images
--     FOR DELETE USING (
--         EXISTS (
--             SELECT 1 FROM upload_sessions us
--             WHERE us.id = uploaded_images.upload_session_id
--               AND us.user_id = auth.uid()
--         )
--     );

-- =============================================================================
-- Helper function: merge profile_data (partial update)
-- =============================================================================
CREATE OR REPLACE FUNCTION merge_profile_data(
    p_workspace_id UUID,
    p_updates JSONB
) RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    UPDATE student_profiles
    SET
        profile_data = profile_data || p_updates,
        updated_at = now()
    WHERE workspace_id = p_workspace_id
    RETURNING profile_data INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- Storage path rule (configure in Supabase Dashboard):
-- uploads/{user_id}/{workspace_id}/{upload_session_id}/{filename}
--
-- Storage RLS policy:
-- CREATE POLICY storage_uploads_policy ON storage.objects
--     FOR ALL USING (
--         bucket_id = 'uploads' AND
--         (storage.foldername(name))[1] = auth.uid()::text
--     );
-- =============================================================================
