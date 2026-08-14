-- Player availability columns for fantasy / squad integrity checks
ALTER TABLE players ADD COLUMN IF NOT EXISTS is_suspended BOOLEAN DEFAULT FALSE;
ALTER TABLE players ADD COLUMN IF NOT EXISTS is_transferred_out BOOLEAN DEFAULT FALSE;
ALTER TABLE players ADD COLUMN IF NOT EXISTS unavailable_reason VARCHAR(255);
ALTER TABLE players ADD COLUMN IF NOT EXISTS status_checked_at TIMESTAMP WITH TIME ZONE;

CREATE TABLE IF NOT EXISTS fantasy_player_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_name VARCHAR(255) NOT NULL,
    team_name VARCHAR(255) NOT NULL,
    fpl_id INT,
    status_code CHAR(1) DEFAULT 'a',
    is_injured BOOLEAN DEFAULT FALSE,
    is_suspended BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE,
    is_transferred BOOLEAN DEFAULT FALSE,
    current_team VARCHAR(255),
    news TEXT,
    chance_this_round INT,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_name, team_name)
);

CREATE INDEX IF NOT EXISTS idx_fantasy_player_status_checked
    ON fantasy_player_status(checked_at DESC);
