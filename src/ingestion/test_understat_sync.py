import asyncio
from src.ingestion.understat_deep_sync import UnderstatDeepSync

async def main():
    syncer = UnderstatDeepSync()
    
    # Fetch actual IDs from DB
    import psycopg2
    import os
    conn = psycopg2.connect(f"dbname=fpredict_db user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} host=localhost")
    cur = conn.cursor()
    cur.execute("SELECT id, team_name FROM teams WHERE team_name IN ('Arsenal', 'Aston Villa')")
    teams = cur.fetchall()
    cur.close()
    conn.close()
    
    print(f"Testing with {len(teams)} teams: {teams}")
    for tid, tname in teams:
        await syncer.sync_team_players(tid, tname)

if __name__ == "__main__":
    asyncio.run(main())
