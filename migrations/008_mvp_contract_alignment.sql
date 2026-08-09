-- Align MVP schema with the canonical services/incidents contract

ALTER TABLE profiles
    ADD COLUMN IF NOT EXISTS subscription_tier TEXT DEFAULT 'free';

ALTER TABLE services
    ADD COLUMN IF NOT EXISTS last_response_time_ms FLOAT;

ALTER TABLE health_checks
    ADD COLUMN IF NOT EXISTS error_message TEXT;
