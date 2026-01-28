-- Migration 007: Week 1 Critical Features
-- Performance Indices + AI Usage + Rate Limiting Tables
-- =====================================================

-- 1. CRITICAL PERFORMANCE INDICES
-- ================================

-- For incident queries (most common)
CREATE INDEX IF NOT EXISTS idx_incidents_detected_at 
  ON incidents(detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_incidents_service_status 
  ON incidents(service_id, status) 
  WHERE status != 'resolved';

CREATE INDEX IF NOT EXISTS idx_incidents_severity 
  ON incidents(severity, detected_at DESC);

-- For health check performance
CREATE INDEX IF NOT EXISTS idx_health_checks_service_checked 
  ON health_checks(service_id, checked_at DESC);

CREATE INDEX IF NOT EXISTS idx_health_checks_status 
  ON health_checks(status) 
  WHERE status != 'healthy';

-- For deployment correlation
CREATE INDEX IF NOT EXISTS idx_deployments_service_time 
  ON deployments(service_id, deployed_at DESC);

-- For user lookups
CREATE INDEX IF NOT EXISTS idx_users_email 
  ON users(email);

-- 2. AI USAGE TRACKING TABLE
-- ==========================

CREATE TABLE IF NOT EXISTS ai_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
    operation TEXT NOT NULL DEFAULT 'unknown',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Metadata
    request_id TEXT,
    error TEXT
);

-- Indices for AI usage queries
CREATE INDEX IF NOT EXISTS idx_ai_usage_user_month 
  ON ai_usage(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_ai_usage_timestamp 
  ON ai_usage(timestamp DESC);

-- 3. RATE LIMIT LOGGING TABLE
-- ===========================

CREATE TABLE IF NOT EXISTS rate_limit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indices for rate limit checks (need to be fast!)
CREATE INDEX IF NOT EXISTS idx_rate_limit_user_action_time 
  ON rate_limit_log(user_id, action, timestamp DESC);

-- Auto-cleanup: Delete rate limit logs older than 7 days
-- Run this as a cron job or scheduled function
-- DELETE FROM rate_limit_log WHERE timestamp < now() - interval '7 days';

-- 4. ADMIN ALERTS TABLE
-- =====================

CREATE TABLE IF NOT EXISTS admin_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info',
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_admin_alerts_unacked 
  ON admin_alerts(acknowledged, created_at DESC)
  WHERE acknowledged = false;

-- 5. RUNBOOK EXECUTION AUDIT LOG
-- ==============================

CREATE TABLE IF NOT EXISTS runbook_executions (
    id TEXT PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    runbook_id UUID NOT NULL REFERENCES runbooks(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'started',
    results JSONB,
    executed_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    
    -- Audit fields
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_runbook_executions_incident 
  ON runbook_executions(incident_id, started_at DESC);

-- 6. CHAOS EXPERIMENT TRACKING
-- ============================

CREATE TABLE IF NOT EXISTS chaos_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    experiment_type TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    results JSONB,
    
    -- Safety fields
    approved BOOLEAN DEFAULT false,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    legal_accepted BOOLEAN DEFAULT false,
    emergency_stopped BOOLEAN DEFAULT false,
    stopped_at TIMESTAMPTZ,
    stopped_by UUID REFERENCES users(id)
);

-- 7. ENHANCE USERS TABLE FOR TIERS
-- ================================

DO $$
BEGIN
    -- Add subscription_tier column if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'subscription_tier'
    ) THEN
        ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free';
    END IF;
    
    -- Add subscription dates
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'subscription_started_at'
    ) THEN
        ALTER TABLE users ADD COLUMN subscription_started_at TIMESTAMPTZ;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'subscription_ends_at'
    ) THEN
        ALTER TABLE users ADD COLUMN subscription_ends_at TIMESTAMPTZ;
    END IF;
    
    -- Add stripe customer ID
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'stripe_customer_id'
    ) THEN
        ALTER TABLE users ADD COLUMN stripe_customer_id TEXT;
    END IF;
END $$;

-- Constraint for subscription tier
ALTER TABLE users DROP CONSTRAINT IF EXISTS check_subscription_tier;
ALTER TABLE users ADD CONSTRAINT check_subscription_tier 
  CHECK (subscription_tier IN ('free', 'pro', 'enterprise'));

-- 8. NOTIFICATION HISTORY (for GDPR export)
-- =========================================

CREATE TABLE IF NOT EXISTS notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    incident_id UUID REFERENCES incidents(id) ON DELETE SET NULL,
    channel TEXT NOT NULL, -- 'email', 'slack', 'pagerduty'
    recipient TEXT NOT NULL,
    subject TEXT,
    content_preview TEXT, -- First 200 chars for audit
    status TEXT NOT NULL DEFAULT 'sent',
    error TEXT,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notification_history_user 
  ON notification_history(user_id, sent_at DESC);

-- 9. VECTOR SEARCH INDEX (for pgvector)
-- =====================================

-- Only create if pgvector extension is enabled
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        -- Create IVFFlat index for fast similarity search
        CREATE INDEX IF NOT EXISTS idx_incidents_embedding_ivfflat 
          ON incidents USING ivfflat (embedding vector_cosine_ops)
          WITH (lists = 100);
    END IF;
END $$;

-- 10. SOFT LIMITS TRACKING
-- ========================

CREATE TABLE IF NOT EXISTS user_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    limit_type TEXT NOT NULL,
    current_value INTEGER NOT NULL DEFAULT 0,
    max_value INTEGER NOT NULL,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE(user_id, limit_type)
);

-- View for easy limit checking
CREATE OR REPLACE VIEW user_limit_status AS
SELECT 
    u.id as user_id,
    u.email,
    u.subscription_tier,
    COALESCE(services.count, 0) as services_count,
    COALESCE(incidents.count, 0) as incidents_this_month,
    COALESCE(ai.total_cost, 0) as ai_cost_this_month
FROM users u
LEFT JOIN (
    SELECT user_id, COUNT(*) as count 
    FROM services 
    GROUP BY user_id
) services ON services.user_id = u.id
LEFT JOIN (
    SELECT user_id, COUNT(*) as count 
    FROM incidents 
    WHERE detected_at >= date_trunc('month', now())
    GROUP BY user_id
) incidents ON incidents.user_id = u.id
LEFT JOIN (
    SELECT user_id, SUM(cost_usd) as total_cost 
    FROM ai_usage 
    WHERE timestamp >= date_trunc('month', now())
    GROUP BY user_id
) ai ON ai.user_id = u.id;

-- Grant appropriate permissions
-- GRANT SELECT ON user_limit_status TO authenticated;

COMMENT ON TABLE ai_usage IS 'Track all AI API calls for cost monitoring';
COMMENT ON TABLE rate_limit_log IS 'Log actions for rate limiting (auto-purged after 7 days)';
COMMENT ON TABLE admin_alerts IS 'Alerts for admins (budget exceeded, abuse, etc)';
COMMENT ON TABLE chaos_experiments IS 'Track chaos engineering experiments with safety fields';
