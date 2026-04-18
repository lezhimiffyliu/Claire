-- Add learning context fields for resume support

ALTER TABLE workspaces
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

ALTER TABLE student_profiles
ADD COLUMN IF NOT EXISTS checkpoint JSONB DEFAULT '{"type": "onboarding"}',
ADD COLUMN IF NOT EXISTS diagnostic_completed BOOLEAN DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_workspaces_user_active
ON workspaces(user_id, is_active) WHERE is_active = true;

-- Enable RLS
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;

-- RLS policies (cast both to text for comparison)
DROP POLICY IF EXISTS "Users see own workspaces" ON workspaces;
CREATE POLICY "Users see own workspaces" ON workspaces
FOR ALL USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users see own profiles" ON student_profiles;
CREATE POLICY "Users see own profiles" ON student_profiles
FOR ALL USING (auth.uid()::text = user_id::text);
