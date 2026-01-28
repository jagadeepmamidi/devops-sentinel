-- Migration 001: Enhance Services Table for Phase 1
-- ==================================================
-- Adds service classification, custom health checks, SSL monitoring

-- Add new columns to services table
ALTER TABLE services
ADD COLUMN IF NOT EXISTS role TEXT CHECK (role IN ('critical', 'canary', 'standard')) DEFAULT 'standard',
ADD COLUMN IF NOT EXISTS criticality_score FLOAT DEFAULT 0.5 CHECK (criticality_score >= 0 AND criticality_score <= 1),
ADD COLUMN IF NOT EXISTS check_type TEXT CHECK (check_type IN ('http', 'script', 'tcp', 'dns', 'ssl')) DEFAULT 'http',
ADD COLUMN IF NOT EXISTS check_script TEXT,
ADD COLUMN IF NOT EXISTS ssl_cert_url TEXT,
ADD COLUMN IF NOT EXISTS ssl_alert_days_before INTEGER[] DEFAULT ARRAY[30, 7],
ADD COLUMN IF NOT EXISTS team_owner TEXT,
ADD COLUMN IF NOT EXISTS slack_channel TEXT,
ADD COLUMN IF NOT EXISTS documentation_url TEXT;

-- Add comments
COMMENT ON COLUMN services.role IS 'Service classification: critical (core), canary (experimental), standard';
COMMENT ON COLUMN services.criticality_score IS 'Impact score from 0.0 (low) to 1.0 (critical)';
COMMENT ON COLUMN services.check_type IS 'Type of health check: http, custom script, tcp, dns, ssl';
COMMENT ON COLUMN services.check_script IS 'Python/Bash script for custom health checks';
COMMENT ON COLUMN services.ssl_cert_url IS 'URL for SSL certificate monitoring';
COMMENT ON COLUMN services.ssl_alert_days_before IS 'Days before expiration to alert';

-- Create index on role and criticality for filtering
CREATE INDEX IF NOT EXISTS idx_services_role ON services(role);
CREATE INDEX IF NOT EXISTS idx_services_criticality ON services(criticality_score DESC);
