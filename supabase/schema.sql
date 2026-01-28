-- DevOps Sentinel - Supabase Schema Migration
-- ============================================
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- ENUMS
-- =============================================================================

CREATE TYPE incident_status AS ENUM ('detecting', 'alerting', 'investigating', 'resolved');
CREATE TYPE incident_severity AS ENUM ('critical', 'high', 'medium', 'low');

-- =============================================================================
-- PROFILES (extends auth.users)
-- =============================================================================

CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE,
    display_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- =============================================================================
-- PROJECTS
-- =============================================================================

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_projects_user_id ON projects(user_id);

-- =============================================================================
-- SERVICES
-- =============================================================================

CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    check_interval INTEGER DEFAULT 10 CHECK (check_interval > 0),
    is_active BOOLEAN DEFAULT true,
    last_status TEXT DEFAULT 'unknown',
    last_checked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_services_user_id ON services(user_id);
CREATE INDEX idx_services_project_id ON services(project_id);

-- =============================================================================
-- INCIDENTS
-- =============================================================================

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    service_id UUID REFERENCES services(id) ON DELETE CASCADE NOT NULL,
    status incident_status DEFAULT 'detecting',
    severity incident_severity DEFAULT 'medium',
    error_code INTEGER,
    error_message TEXT,
    detected_at TIMESTAMPTZ DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    mttd_seconds FLOAT,
    mttr_seconds FLOAT,
    investigation_report TEXT,
    action_plan TEXT,
    postmortem TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_incidents_user_id ON incidents(user_id);
CREATE INDEX idx_incidents_service_id ON incidents(service_id);
CREATE INDEX idx_incidents_detected_at ON incidents(detected_at DESC);
CREATE INDEX idx_incidents_status ON incidents(status);

-- =============================================================================
-- HEALTH CHECKS
-- =============================================================================

CREATE TABLE health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID REFERENCES services(id) ON DELETE CASCADE NOT NULL,
    status_code INTEGER,
    response_time_ms FLOAT,
    is_healthy BOOLEAN,
    checked_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_health_checks_service_id ON health_checks(service_id);
CREATE INDEX idx_health_checks_checked_at ON health_checks(checked_at DESC);

-- =============================================================================
-- ROW LEVEL SECURITY
-- =============================================================================

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE services ENABLE ROW LEVEL SECURITY;
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_checks ENABLE ROW LEVEL SECURITY;

-- Profiles: users can only see/edit their own
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- Projects: users can manage their own
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create projects" ON projects
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE USING (auth.uid() = user_id);

-- Services: users can manage their own
CREATE POLICY "Users can view own services" ON services
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create services" ON services
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own services" ON services
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own services" ON services
    FOR DELETE USING (auth.uid() = user_id);

-- Incidents: users can view their own
CREATE POLICY "Users can view own incidents" ON incidents
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create incidents" ON incidents
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own incidents" ON incidents
    FOR UPDATE USING (auth.uid() = user_id);

-- Health checks: linked to service ownership
CREATE POLICY "Users can view health checks for own services" ON health_checks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM services s 
            WHERE s.id = health_checks.service_id 
            AND s.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create health checks for own services" ON health_checks
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM services s 
            WHERE s.id = health_checks.service_id 
            AND s.user_id = auth.uid()
        )
    );

-- =============================================================================
-- UPDATED_AT TRIGGER
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER services_updated_at
    BEFORE UPDATE ON services
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
