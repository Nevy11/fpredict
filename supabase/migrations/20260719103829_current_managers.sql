CREATE TABLE IF NOT EXISTS current_managers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_name VARCHAR(255) UNIQUE NOT NULL,
    manager_name VARCHAR(255) NOT NULL,
    tactical_style VARCHAR(50),
    last_5_games JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);
