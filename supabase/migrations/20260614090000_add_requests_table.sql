CREATE TABLE IF NOT EXISTS prediction_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    home_team_id UUID REFERENCES teams(id),
    away_team_id UUID REFERENCES teams(id),
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Grant permissions for API access
GRANT ALL PRIVILEGES ON TABLE public.prediction_requests TO anon, authenticated, service_role;

-- Reload Schema
NOTIFY pgrst, 'reload schema';
