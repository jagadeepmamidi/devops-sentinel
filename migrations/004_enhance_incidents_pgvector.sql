-- Migration 004: Enhance Incidents Table + Add pgvector
-- ========================================================
-- Adds severity levels, confidence scoring, incident memory with pgvector

-- Enable pgvector extension for similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enhance incidents table
ALTER TABLE incidents
ADD COLUMN IF NOT EXISTS severity TEXT CHECK (severity IN ('P0', 'P1', 'P2', 'P3')) DEFAULT 'P2',
ADD COLUMN IF NOT EXISTS confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
ADD COLUMN IF NOT EXISTS failure_type TEXT CHECK (failure_type IN ('transient', 'dependency', 'deployment', 'resource_exhaustion', 'anomaly', 'unknown')),
ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS blast_radius INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS affected_services UUID[],
ADD COLUMN IF NOT EXISTS similar_incidents UUID[],
ADD COLUMN IF NOT EXISTS deployment_id UUID,
ADD COLUMN IF NOT EXISTS suggested_rollback BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS rollback_version TEXT,
ADD COLUMN IF NOT EXISTS matched_runbook_id UUID,
ADD COLUMN IF NOT EXISTS assigned_to TEXT,
ADD COLUMN IF NOT EXISTS slack_thread_ts TEXT,
ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS mttd_seconds INTEGER,
ADD COLUMN IF NOT EXISTS mtta_seconds INTEGER,
ADD COLUMN IF NOT EXISTS mttr_seconds INTEGER,
ADD COLUMN IF NOT EXISTS embedding vector(384);  -- Hugging Face all-MiniLM-L6-v2

-- Comments
COMMENT ON COLUMN incidents.severity IS 'P0=critical, P1=high, P2=medium, P3=low';
COMMENT ON COLUMN incidents.confidence_score IS 'Classifier confidence (0-1) for incident validity';
COMMENT ON COLUMN incidents.blast_radius IS 'Number of affected downstream services';
COMMENT ON COLUMN incidents.embedding IS 'Vector embedding for similarity search (384-dim)';
COMMENT ON COLUMN incidents.mttd_seconds IS 'Mean Time To Detect';
COMMENT ON COLUMN incidents.mtta_seconds IS 'Mean Time To Acknowledge';
COMMENT ON COLUMN incidents.mttr_seconds IS 'Mean Time To Resolve';

-- Indexes
CREATE INDEX idx_incidents_severity ON incidents(severity, status);
CREATE INDEX idx_incidents_confidence ON incidents(confidence_score DESC);
CREATE INDEX idx_incidents_assigned ON incidents(assigned_to, status);
CREATE INDEX idx_incidents_deployment ON incidents(deployment_id);

-- pgvector index for similarity search (IVFFlat with cosine distance)
-- Note: Build after inserting ~1000 rows for better performance
CREATE INDEX idx_incidents_embedding ON incidents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Function for vector similarity search
CREATE OR REPLACE FUNCTION match_incidents(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    service_name TEXT,
    root_cause TEXT,
    remediation_steps TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        s.name as service_name,
        i.root_cause,
        i.remediation_steps,
        1 - (i.embedding <=> query_embedding) AS similarity
    FROM incidents i
    JOIN services s ON i.service_id = s.id
    WHERE 
        i.embedding IS NOT NULL
        AND i.status = 'resolved'
        AND 1 - (i.embedding <=> query_embedding) > match_threshold
    ORDER BY i.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_incidents IS 'Find similar resolved incidents using vector similarity';
