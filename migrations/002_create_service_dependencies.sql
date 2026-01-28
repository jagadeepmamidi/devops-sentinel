-- Migration 002: Create Service Dependencies Table
-- ==================================================
-- Enables dependency graph analysis and cascade failure prediction

CREATE TABLE IF NOT EXISTS service_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    child_service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    dependency_type TEXT CHECK (dependency_type IN ('hard', 'soft', 'optional')) DEFAULT 'hard',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    -- Prevent self-dependencies and duplicates
    UNIQUE(parent_service_id, child_service_id),
    CHECK (parent_service_id != child_service_id)
);

-- Comments
COMMENT ON TABLE service_dependencies IS 'Service dependency relationships for cascade analysis';
COMMENT ON COLUMN service_dependencies.parent_service_id IS 'Service that provides the dependency';
COMMENT ON COLUMN service_dependencies.child_service_id IS 'Service that depends on parent';
COMMENT ON COLUMN service_dependencies.dependency_type IS 'hard=critical, soft=degrades gracefully, optional=non-essential';

-- Indexes for graph traversal
CREATE INDEX idx_dependencies_parent ON service_dependencies(parent_service_id);
CREATE INDEX idx_dependencies_child ON service_dependencies(child_service_id);
CREATE INDEX idx_dependencies_type ON service_dependencies(dependency_type);

-- Function to prevent circular dependencies
CREATE OR REPLACE FUNCTION check_circular_dependency()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if adding this edge would create a cycle
    IF EXISTS (
        WITH RECURSIVE dep_tree AS (
            SELECT child_service_id AS service_id
            FROM service_dependencies
            WHERE parent_service_id = NEW.child_service_id
            
            UNION
            
            SELECT sd.child_service_id
            FROM service_dependencies sd
            INNER JOIN dep_tree dt ON sd.parent_service_id = dt.service_id
        )
        SELECT 1 FROM dep_tree WHERE service_id = NEW.parent_service_id
    ) THEN
        RAISE EXCEPTION 'Circular dependency detected: % -> %', NEW.parent_service_id, NEW.child_service_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_circular_dependencies
BEFORE INSERT OR UPDATE ON service_dependencies
FOR EACH ROW EXECUTE FUNCTION check_circular_dependency();
