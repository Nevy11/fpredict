import psycopg2
import os
import uuid
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

def populate_mock_roster():
    conn = psycopg2.connect(LOCAL_DB_URL)
    cur = conn.cursor()
    
    cur.execute("SELECT id, team_name FROM teams")
    teams = cur.fetchall()
    
    players = []
    memberships = []
    
    for tid, name in teams:
        # Create 5 players per team
        for i in range(5):
            pid = str(uuid.uuid4())
            players.append((pid, tid, f"{name} Player {i+1}", False, 'FW'))
            memberships.append((pid, tid, '2026-06-13'))
            
    cur.executemany(
        "INSERT INTO players (id, team_id, name, is_injured, position) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", 
        players
    )
    cur.executemany(
        "INSERT INTO squad_membership (player_id, team_id, joined_date) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", 
        memberships
    )
    
    conn.commit()
    print(f"Inserted {len(players)} players and memberships.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    populate_mock_roster()
