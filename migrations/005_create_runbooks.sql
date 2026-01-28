-- Migration 005: Create Runbooks Table
-- ======================================
-- Runbooks/playbooks with effectiveness tracking

CREATE TABLE IF NOT EXISTS runbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE,
    
    title TEXT NOT NULL,
    description TEXT,
    
    -- Matching Criteria
    error_pattern TEXT,  -- Regex pattern to match error messages
    tags TEXT[] DEFAULT '{}',
    
    -- Steps (JSONB array)
    steps JSONB NOT NULL DEFAULT '[]',
    -- Format: [{"title": "...", "command": "...", "description": "..."}]
    
    -- Effectiveness Tracking
    times_used INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    success_rate FLOAT GENERATED ALWAYS AS (
        CASE WHEN times_used > 0 THEN success_count::FLOAT / times_used ELSE 0 END
    ) STORED,
    
    -- Metadata
    created_by TEXT,
    last_updated_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE runbooks IS 'Incident response playbooks with automatic matching';
COMMENT ON COLUMN runbooks.error_pattern IS 'Regex pattern to match against error messages';
COMMENT ON COLUMN runbooks.steps IS 'Array of steps: [{title, command, description}]';
COMMENT ON COLUMN runbooks.success_rate IS 'Auto-calculated success rate from usage';

-- Indexes
CREATE INDEX idx_runbooks_service ON runbooks(service_id);
CREATE INDEX idx_runbooks_success_rate ON runbooks(success_rate DESC);
CREATE INDEX idx_runbooks_tags ON runbooks USING GIN(tags);

-- Function to record runbook usage
CREATE OR REPLACE FUNCTION record_runbook_usage(
    runbook_uuid UUID,
    was_successful BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    UPDATE runbooks
    SET 
        times_used = times_used + 1,
        success_count = success_count + (CASE WHEN was_successful THEN 1 ELSE 0 END),
        last_updated_at = now()
    WHERE id = runbook_uuid;
END;
$$ LANGUAGE plpgsql;

-- Sample runbook for testing
INSERT INTO runbooks (service_id, title, description, error_pattern, tags, steps, created_by)
VALUES (
    NULL,  -- Global runbook
    'Database Connection Pool Exhausted',
    'Steps to resolve database connection pool issues',
    'connection pool.*exhausted|too many connections',
    ARRAY['database', 'connection', 'postgres'],
    '[
        {"title": "Check current connections", "command": "SELECT count(*) FROM pg_stat_activity;", "description": "Count active database connections"},
        {"title": "Kill idle connections", "command": "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = ''idle'';", "description": "Terminate idle connections"},
        {"title": "Restart application", "command": "kubectl rollout restart deployment", "description": "Restart to reset connection pool"}
    ]'::JSONB,
    'system'
) ON CONFLICT DO NOTHING;
