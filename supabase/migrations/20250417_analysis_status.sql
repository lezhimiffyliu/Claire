-- Migration: Add analysis_status and analysis_result to upload_sessions
-- Date: 2025-04-17
-- Purpose: Track analysis state for efficient polling (no more querying uploaded_images)

-- Add analysis_status column with default 'pending'
ALTER TABLE upload_sessions
ADD COLUMN IF NOT EXISTS analysis_status TEXT NOT NULL DEFAULT 'pending';

-- Add analysis_result column to store analysis results as JSON
ALTER TABLE upload_sessions
ADD COLUMN IF NOT EXISTS analysis_result JSONB;

-- Add index for efficient polling on analysis_status
CREATE INDEX IF NOT EXISTS idx_upload_sessions_analysis_status
ON upload_sessions(analysis_status);

-- Add comment explaining the status values
COMMENT ON COLUMN upload_sessions.analysis_status IS 'Analysis state: pending|running|completed|failed';
COMMENT ON COLUMN upload_sessions.analysis_result IS 'JSON result from vision analysis (stored when completed)';
