-- Migration 006: Create Phase 2 Tables (Anomalies, Deployments, On-Call)
-- =========================================================================

-- Anomalies Table (ML Detections)
CREATE TABLE IF NOT EXISTS anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    
    anomaly_type TEXT CHECK (anomaly_type IN ('response_time', 'error_rate', 'traffic', 'mixed')) NOT NULL,
    metric_value FLOAT NOT NULL,
    baseline_value FLOAT NOT NULL,
    deviation_score FLOAT NOT NULL,  -- How many std deviations from baseline
    
    anomaly_score FLOAT CHECK (anomaly_score >= -1 AND anomaly_score <= 1),  -- Isolation Forest score
    is_critical BOOLEAN DEFAULT false,
    
    context JSONB,  -- Additional context about the anomaly
    
    created_incident_id UUID REFERENCES incidents(id),
    detected_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_anomalies_service ON anomalies(service_id, detected_at DESC);
CREATE INDEX idx_anomalies_critical ON anomalies(is_critical, detected_at DESC);

COMMENT ON TABLE anomalies IS 'ML-detected anomalies from Isolation Forest';
COMMENT ON COLUMN anomalies.anomaly_score IS 'Isolation Forest anomaly score (-1 to 1, lower = more anomalous)';

-- Enhanced Deployments Table
CREATE TABLE IF NOT EXISTS deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    
    version TEXT NOT NULL,
    previous_version TEXT,
    
    deployment_type TEXT CHECK (deployment_type IN ('rolling', 'blue_green', 'canary', 'manual')) DEFAULT 'rolling',
    deployment_tool TEXT,  -- 'github-actions', 'argocd', 'kubernetes', 'manual'
    
    triggered_by TEXT,
    commit_sha TEXT,
    commit_message TEXT,
    repository_url TEXT,
    
    -- Status Tracking
    status TEXT CHECK (status IN ('in_progress', 'succeeded', 'failed', 'rolled_back')) DEFAULT 'in_progress',
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    
    -- Incident Correlation
    related_incidents UUID[],
    caused_incident BOOLEAN DEFAULT false,
    rollback_recommended BOOLEAN DEFAULT false,
    
    -- Success Metrics
    error_rate_pre FLOAT,
    error_rate_post FLOAT,
    response_time_pre FLOAT,
    response_time_post FLOAT
);

CREATE INDEX idx_deployments_service ON deployments(service_id, started_at DESC);
CREATE INDEX idx_deployments_status ON deployments(status);
CREATE INDEX idx_deployments_caused_incident ON deployments(caused_incident);

COMMENT ON TABLE deployments IS 'Deployment tracking for rollback correlation';

-- On-Call Schedules Table
CREATE TABLE IF NOT EXISTS on_call_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    team_name TEXT NOT NULL,
    user_email TEXT NOT NULL, -- Or user_id if you have user management
    user_name TEXT,
    user_phone TEXT,
    user_slack_id TEXT,
    
    -- Schedule
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    
    -- Priority (for escalation)
    priority INTEGER DEFAULT 1 CHECK (priority >= 1 AND priority <= 5),  -- 1=primary, 2=secondary, etc.
    
    -- Filters (which incidents this person handles)
    severity_levels TEXT[] DEFAULT ARRAY['P0', 'P1', 'P2', 'P3'],
    service_ids UUID[],
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_on_call_active ON on_call_schedules(is_active, starts_at, ends_at);
CREATE INDEX idx_on_call_team ON on_call_schedules(team_name);

COMMENT ON TABLE on_call_schedules IS 'On-call rotation schedules for incident assignment';

-- Function to get current on-call person
CREATE OR REPLACE FUNCTION get_current_on_call(
    incident_severity TEXT,
    incident_service_id UUID
)
RETURNS TABLE (
    user_email TEXT,
    user_name TEXT,
    user_slack_id TEXT,
    priority INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ocs.user_email,
        ocs.user_name,
        ocs.user_slack_id,
        ocs.priority
    FROM on_call_schedules ocs
    WHERE 
        ocs.is_active = true
        AND now() BETWEEN ocs.starts_at AND ocs.ends_at
        AND incident_severity = ANY(ocs.severity_levels)
        AND (ocs.service_ids IS NULL OR incident_service_id = ANY(ocs.service_ids))
    ORDER BY ocs.priority
    LIMIT 1;
END;
$$;

-- Incident Timeline (Comments & Actions)
CREATE TABLE IF NOT EXISTS incident_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    
    event_type TEXT CHECK (event_type IN ('comment', 'status_change', 'assignment', 'runbook_executed', 'deployment')) NOT NULL,
    
    author TEXT,  -- Email or user ID
    content TEXT,
    
    metadata JSONB,  -- Additional event-specific data
    
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_timeline_incident ON incident_timeline(incident_id, created_at DESC);

COMMENT ON TABLE incident_timeline IS 'Timeline of comments and actions on incidents';

-- Incident Participants (Collaboration)
CREATE TABLE IF NOT EXISTS incident_participants (
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    user_email TEXT NOT NULL,
    user_name TEXT,
    role TEXT CHECK (role IN ('assigned', 'collaborator', 'observer')) DEFAULT 'observer',
    joined_at TIMESTAMPTZ DEFAULT now(),
    
    PRIMARY KEY (incident_id, user_email)
);

CREATE INDEX idx_participants_user ON incident_participants(user_email);

COMMENT ON TABLE incident_participants IS 'Track who is working on each incident';
