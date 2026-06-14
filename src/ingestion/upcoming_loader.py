import psycopg2
import os
import uuid
import json
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

def ingest_upcoming_data():
    conn = psycopg2.connect(LOCAL_DB_URL)
    cur = conn.cursor()
    
    # 1. Ingest Fixtures
    cur.execute("SELECT team_name, id FROM teams WHERE team_name IN ('Arsenal', 'Man City', 'Liverpool', 'Chelsea', 'Tottenham', 'Man United')")
    t_map = dict(cur.fetchall())
    
    if len(t_map) < 6:
        print("Required teams not found in DB.")
        return

    fixtures = []
    start_date = date(2026, 8, 15)
    match_ups = [('Arsenal', 'Man City'), ('Liverpool', 'Chelsea'), ('Man United', 'Tottenham'), ('Chelsea', 'Arsenal'), ('Man City', 'Liverpool')]
    
    for i, (h, a) in enumerate(match_ups):
        fixtures.append((str(start_date + timedelta(days=i*7)), t_map[h], t_map[a], 'EPL'))
        
    cur.executemany(
        "INSERT INTO match_records (match_date, home_team_id, away_team_id, competition, home_goals, away_goals) VALUES (%s, %s, %s, %s, NULL, NULL)", 
        fixtures
    )
    
    # 2. Populate Player Metadata (Ensure players exist first)
    players_to_add = [
        ('Bukayo Saka', 'Arsenal', 24, True, '{"world_cup": "finalist"}', 0.98, '["set-pieces", "dribbling"]'),
        ('Kevin De Bruyne', 'Man City', 34, False, '{"world_cup": "semis"}', 0.92, '["passing", "vision"]')
    ]
    
    for p_name, t_name, age, captain, status, mindset, skills in players_to_add:
        tid = t_map[t_name]
        # Insert player if not exists
        cur.execute("INSERT INTO players (name, team_id) VALUES (%s, %s) ON CONFLICT (name, team_id) DO UPDATE SET last_updated = NOW() RETURNING id", (p_name, tid))
        pid = cur.fetchone()[0]
        
        # Insert metadata
        cur.execute(
            """INSERT INTO player_metadata (player_id, age, is_captain, international_status, mindset_score, skill_tags) 
               VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (player_id) DO UPDATE SET age = EXCLUDED.age""",
            (pid, age, captain, status, mindset, skills)
        )
        
    conn.commit()
    print("Ingested upcoming fixtures and player metadata successfully.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    ingest_upcoming_data()
