-- Migration 003: Create Service Baselines Table
-- ================================================
-- Statistical baselines for degraded state detection

CREATE TABLE IF NOT EXISTS service_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    
    -- Statistical Metrics
    avg_response_time_ms FLOAT NOT NULL,
    p50_response_time_ms FLOAT NOT NULL,
    p95_response_time_ms FLOAT NOT NULL,
    p99_response_time_ms FLOAT NOT NULL,
    stddev_response_time_ms FLOAT NOT NULL,
    
    error_rate FLOAT DEFAULT 0.0 CHECK (error_rate >= 0 AND error_rate <= 1),
    request_rate FLOAT DEFAULT 0.0,
    
    -- Metadata
    sample_size INTEGER NOT NULL CHECK (sample_size > 0),
    calculated_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    
    -- Only one active baseline per service at a time
    UNIQUE(service_id, calculated_at)
);

COMMENT ON TABLE service_baselines IS 'Statistical baselines for anomaly and degradation detection';
COMMENT ON COLUMN service_baselines.p95_response_time_ms IS '95th percentile response time';
COMMENT ON COLUMN service_baselines.p99_response_time_ms IS '99th percentile response time';
COMMENT ON COLUMN service_baselines.stddev_response_time_ms IS 'Standard deviation for anomaly detection';

-- Indexes
CREATE INDEX idx_baselines_service ON service_baselines(service_id);
CREATE INDEX idx_baselines_expires ON service_baselines(expires_at);

-- Function to get latest baseline for a service
CREATE OR REPLACE FUNCTION get_latest_baseline(service_uuid UUID)
RETURNS service_baselines AS $$
    SELECT *
    FROM service_baselines
    WHERE service_id = service_uuid
    AND expires_at > now()
    ORDER BY calculated_at DESC
    LIMIT 1;
$$ LANGUAGE SQL;
