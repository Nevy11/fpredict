-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Teams Lookup Table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_name VARCHAR(255) UNIQUE NOT NULL,
    manager_name VARCHAR(255),
    tactical_style_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    elo_rating INT DEFAULT 1500,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 2. Players Table
CREATE TABLE IF NOT EXISTS players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    is_injured BOOLEAN DEFAULT FALSE,
    position VARCHAR(50),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Match Records
CREATE TABLE IF NOT EXISTS match_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_date DATE NOT NULL,
    competition VARCHAR(100),
    home_team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    away_team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    home_goals INT,
    away_goals INT,
    home_xg NUMERIC(4,2),
    away_xg NUMERIC(4,2),
    odds_home NUMERIC(5,2),
    odds_draw NUMERIC(5,2),
    odds_away NUMERIC(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 4. Feature Store
CREATE TABLE IF NOT EXISTS feature_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    features JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 5. Unstructured News Storage
CREATE TABLE IF NOT EXISTS unstructured_news (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    source_name VARCHAR(100),
    published_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    raw_text TEXT NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    extracted_entities JSONB DEFAULT '{}'::jsonb,
    sentiment_score NUMERIC(3,2)
);

-- 6. Player Performance History
CREATE TABLE IF NOT EXISTS player_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    match_id UUID REFERENCES match_records(id) ON DELETE CASCADE,
    minutes_played INT,
    xg_contribution NUMERIC(4,2),
    progressive_passes INT,
    pressing_regains INT,
    rating_score NUMERIC(4,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 7. Squad Membership
CREATE TABLE IF NOT EXISTS squad_membership (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    joined_date DATE NOT NULL,
    left_date DATE,
    contract_status VARCHAR(50)
);

-- 8. Impact Metrics
CREATE TABLE IF NOT EXISTS player_impact_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    impact_score NUMERIC(5,4),
    UNIQUE(player_id, snapshot_date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_matches_date ON match_records(match_date);
CREATE INDEX IF NOT EXISTS idx_feature_store_team_date ON feature_store(team_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_news_processed ON unstructured_news(processed);
CREATE INDEX IF NOT EXISTS idx_player_perf_match ON player_performance(match_id);
CREATE INDEX IF NOT EXISTS idx_squad_membership_team ON squad_membership(team_id, joined_date, left_date);
CREATE INDEX IF NOT EXISTS idx_player_impact ON player_impact_metrics(player_id, snapshot_date);
NOTIFY pgrst, 'reload schema';
