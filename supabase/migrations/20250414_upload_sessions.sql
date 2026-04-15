-- Migration: Add upload_sessions and uploaded_images tables
-- Date: 2025-04-14

-- =============================================================================
-- Table: upload_sessions
-- =============================================================================
CREATE TABLE IF NOT EXISTS upload_sessions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id               UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash            TEXT NOT NULL UNIQUE,
    solve_session_id      TEXT NOT NULL,
    question_id           TEXT NOT NULL,
    course                TEXT NOT NULL,
    status                TEXT NOT NULL DEFAULT 'waiting',  -- waiting|paired|receiving_images|closed|expired
    problem_display_text  TEXT,
    mobile_paired_at      TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at            TIMESTAMPTZ NOT NULL,
    closed_at             TIMESTAMPTZ,
    workspace_id          UUID REFERENCES workspaces(id)  -- nullable for now
);

CREATE INDEX IF NOT EXISTS idx_upload_sessions_user_id ON upload_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_token_hash ON upload_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_question_id ON upload_sessions(question_id);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_status ON upload_sessions(status);

-- =============================================================================
-- Table: uploaded_images
-- =============================================================================
CREATE TABLE IF NOT EXISTS uploaded_images (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_session_id   UUID NOT NULL REFERENCES upload_sessions(id) ON DELETE CASCADE,
    storage_path        TEXT NOT NULL,
    filename            TEXT NOT NULL,
    content_type        TEXT NOT NULL,
    size_bytes          INTEGER NOT NULL,
    sequence_number     INTEGER NOT NULL DEFAULT 1,
    uploaded_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_uploaded_images_session_id ON uploaded_images(upload_session_id);

-- =============================================================================
-- RLS Policies
-- =============================================================================

ALTER TABLE upload_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE uploaded_images ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- upload_sessions: user_id = auth.uid()
-- -----------------------------------------------------------------------------
CREATE POLICY upload_sessions_select ON upload_sessions
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY upload_sessions_insert ON upload_sessions
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY upload_sessions_update ON upload_sessions
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY upload_sessions_delete ON upload_sessions
    FOR DELETE USING (user_id = auth.uid());

-- -----------------------------------------------------------------------------
-- uploaded_images: EXISTS check on upload_session
-- -----------------------------------------------------------------------------
CREATE POLICY uploaded_images_select ON uploaded_images
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM upload_sessions us
            WHERE us.id = uploaded_images.upload_session_id
              AND us.user_id = auth.uid()
        )
    );

CREATE POLICY uploaded_images_insert ON uploaded_images
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM upload_sessions us
            WHERE us.id = uploaded_images.upload_session_id
              AND us.user_id = auth.uid()
        )
    );

CREATE POLICY uploaded_images_delete ON uploaded_images
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM upload_sessions us
            WHERE us.id = uploaded_images.upload_session_id
              AND us.user_id = auth.uid()
        )
    );

-- =============================================================================
-- Storage bucket (run in Supabase Dashboard if not exists)
-- =============================================================================
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('uploads', 'uploads', false)
-- ON CONFLICT (id) DO NOTHING;
