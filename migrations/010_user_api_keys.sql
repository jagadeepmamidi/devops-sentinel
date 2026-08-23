-- Encrypted provider credentials. Plain API keys never persist.
CREATE TABLE IF NOT EXISTS user_api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('openrouter', 'openai', 'anthropic')),
    encrypted_api_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, provider)
);

ALTER TABLE user_api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert own encrypted API keys" ON user_api_keys
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own encrypted API keys" ON user_api_keys
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can view own encrypted API keys" ON user_api_keys
    FOR SELECT USING (auth.uid() = user_id);

CREATE TRIGGER user_api_keys_updated_at
    BEFORE UPDATE ON user_api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
