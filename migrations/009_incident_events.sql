-- Add incident event history for auditing and postmortem timelines

CREATE TABLE IF NOT EXISTS incident_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE NOT NULL,
    service_id UUID REFERENCES services(id) ON DELETE CASCADE NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_incident_events_incident_created_at
    ON incident_events(incident_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_incident_events_user_created_at
    ON incident_events(user_id, created_at DESC);

ALTER TABLE incident_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own incident events" ON incident_events
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own incident events" ON incident_events
    FOR INSERT WITH CHECK (auth.uid() = user_id);
