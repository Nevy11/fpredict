import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
# Using the connection details for Supabase
DB_HOST = "db.agojvvfjajkkpqohehcm.supabase.co"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "Skyworth.95"
DB_PORT = "5432"

def update_remote_schema():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        sql = """
        -- 1. Add columns
        ALTER TABLE teams ADD COLUMN IF NOT EXISTS understat_id VARCHAR(100);
        ALTER TABLE players ADD COLUMN IF NOT EXISTS understat_id VARCHAR(100);
        ALTER TABLE match_records ADD COLUMN IF NOT EXISTS understat_id VARCHAR(100);

        -- 2. Create tables
        CREATE TABLE IF NOT EXISTS player_metadata (
            player_id UUID PRIMARY KEY REFERENCES players(id) ON DELETE CASCADE,
            age INT,
            is_captain BOOLEAN DEFAULT FALSE,
            international_status JSONB DEFAULT '{}'::jsonb,
            mindset_score NUMERIC(3,2) DEFAULT 0.0,
            skill_tags JSONB DEFAULT '[]'::jsonb,
            last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS predictions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            match_id UUID REFERENCES match_records(id) ON DELETE CASCADE,
            prediction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            win_probability JSONB,
            predicted_goals_home NUMERIC(3,2),
            predicted_goals_away NUMERIC(3,2),
            predicted_corners NUMERIC(4,2),
            predicted_shots NUMERIC(4,2),
            predicted_scorers JSONB DEFAULT '[]'::jsonb,
            tactical_narrative TEXT,
            version_id VARCHAR(50),
            UNIQUE(match_id, version_id)
        );

        CREATE TABLE IF NOT EXISTS h2h_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            team_a UUID REFERENCES teams(id),
            team_b UUID REFERENCES teams(id),
            total_matches INT,
            a_wins INT,
            b_wins INT,
            avg_goals NUMERIC(3,2),
            UNIQUE(team_a, team_b)
        );

        -- 3. Trigger reload
        NOTIFY pgrst, 'reload schema';
        """
        
        cur.execute(sql)
        conn.commit()
        print("Remote Supabase schema updated successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error updating remote schema: {e}")

if __name__ == "__main__":
    update_remote_schema()
