import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from supabase import create_client
from src.parsing.fbref_parser import FBrefParser
from src.ingestion.fast_scraper import FastScraper

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class SquadLoader:
    def __init__(self):
        self.supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SERVICE_ROLE_KEY"))
        self.local_conn = psycopg2.connect(LOCAL_DB_URL)
        self.parser = FBrefParser()
        self.scraper = FastScraper()

    def get_team_id(self, team_name):
        # FBref to DB name mapping might be needed here
        with self.local_conn.cursor() as cur:
            cur.execute("SELECT id FROM teams WHERE team_name ILIKE %s", (f"%{team_name}%",))
            res = cur.fetchone()
            return res[0] if res else None

    async def fetch_and_persist_squads(self):
        # FBref Standard Stats URL for EPL
        url = "https://fbref.com/en/comps/9/stats/Premier-League-Stats"
        print(f"Fetching squad data from {url}...")
        
        html = await self.scraper.get_raw_data(url)
        if not html:
            print("Failed to fetch FBref data.")
            return

        df = self.parser.parse_squad_stats(html)
        if df is None: return

        # FBref 'Standard Stats' table has 'Player' and 'Squad' columns
        # We need to clean the multi-index if it exists
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(1)

        print(f"Found {len(df)} players. Starting ingestion...")

        for _, row in df.iterrows():
            player_name = row['Player']
            team_name = row['Squad']
            
            if player_name == "Player": continue # Header row in some FBref tables

            team_id = self.get_team_id(team_name)
            if not team_id:
                continue

            # 1. Insert Player
            with self.local_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO players (name, team_id) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING id",
                    (player_name, team_id)
                )
                res = cur.fetchone()
                player_id = res[0] if res else None
                if not player_id: # Get existing ID if conflict
                    cur.execute("SELECT id FROM players WHERE name = %s AND team_id = %s", (player_name, team_id))
                    player_id = cur.fetchone()[0]

                # 2. Insert Squad Membership
                cur.execute(
                    "INSERT INTO squad_membership (player_id, team_id, joined_date) VALUES (%s, %s, CURRENT_DATE) ON CONFLICT DO NOTHING",
                    (player_id, team_id)
                )
            self.local_conn.commit()

            # 3. Supabase Sync (Simplified)
            try:
                self.supabase.table("players").upsert({"name": player_name, "team_id": str(team_id)}).execute()
            except:
                pass

        print("Squad ingestion complete.")

if __name__ == "__main__":
    import asyncio
    loader = SquadLoader()
    asyncio.run(loader.fetch_and_persist_squads())
