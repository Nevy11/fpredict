import os
import pandas as pd
import asyncio
import psycopg2
from src.ingestion.browser_scraper import BrowserScraper
from src.parsing.understat_parser import UnderstatParser
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class UnderstatDeepSync:
    def __init__(self):
        self.scraper = BrowserScraper()
        self.parser = UnderstatParser()
        self.conn = psycopg2.connect(LOCAL_DB_URL)
        self.team_map = {
            "Manchester City": "Manchester_City",
            "Man City": "Manchester_City",
            "Manchester United": "Manchester_United",
            "Man United": "Manchester_United",
            "Newcastle United": "Newcastle_United",
            "Newcastle": "Newcastle_United",
            "Tottenham Hotspur": "Tottenham",
            "Tottenham": "Tottenham",
            "Wolverhampton Wanderers": "Wolverhampton_Wanderers",
            "Wolves": "Wolverhampton_Wanderers",
            "Brighton & Hove Albion": "Brighton",
            "Brighton": "Brighton",
            "West Ham United": "West_Ham",
            "West Ham": "West_Ham",
            "Leicester City": "Leicester",
            "Leicester": "Leicester",
            "Nott'm Forest": "Nottingham_Forest",
            "Nottingham Forest": "Nottingham_Forest",
            "Sheffield United": "Sheffield_United",
            "Aston Villa": "Aston_Villa",
            "Crystal Palace": "Crystal_Palace",
            "West Brom": "West_Bromwich_Albion",
            "Norwich": "Norwich",
            "Luton": "Luton",
            "Ipswich": "Ipswich",
            "Fulham": "Fulham",
            "Bournemouth": "Bournemouth",
            "Everton": "Everton",
            "Brentford": "Brentford",
            "Liverpool": "Liverpool",
            "Chelsea": "Chelsea",
            "Arsenal": "Arsenal"
        }

    def resolve_team_name(self, db_name):
        if db_name in self.team_map:
            return self.team_map[db_name]
        return db_name.replace(" ", "_")

    async def sync_team_players(self, team_id, team_name, year="2024"):
        u_name = self.resolve_team_name(team_name)
        url = f"https://understat.com/team/{u_name}/{year}"
        print(f"Syncing players for {team_name} from {url}...")
        
        html = await self.scraper.get_raw_data(url)
        if not html: return

        df = self.parser.parse_player_table(html)
        if df is None or df.empty:
            print(f"No player data found for {team_name}")
            return

        print(f"Found {len(df)} players. Saving...")
        
        with self.conn.cursor() as cur:
            for _, row in df.iterrows():
                try:
                    p_name = str(row['Player'])
                    pos = str(row['Pos'])
                    
                    xg_raw = str(row['xG'])
                    xg_base = xg_raw.split('+')[0].split('-')[0]
                    xg = float(xg_base)
                    
                    # Clamp for numeric(5,4)
                    if xg > 9.999: xg = 9.999
                    
                    # 1. Update/Insert Player
                    cur.execute(
                        "INSERT INTO players (name, team_id, position) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING RETURNING id",
                        (p_name, team_id, pos)
                    )
                    res = cur.fetchone()
                    p_uuid = res[0] if res else None
                    if not p_uuid:
                        cur.execute("SELECT id FROM players WHERE name = %s AND team_id = %s", (p_name, team_id))
                        p_uuid = cur.fetchone()[0]

                    # 2. Add Performance Snapshot
                    cur.execute(
                        "INSERT INTO player_impact_metrics (player_id, snapshot_date, impact_score) VALUES (%s, CURRENT_DATE, %s) ON CONFLICT (player_id, snapshot_date) DO UPDATE SET impact_score = %s",
                        (p_uuid, xg, xg)
                    )
                except Exception as e:
                    print(f"Error saving player {row.get('Player')}: {e}")
                    continue
            self.conn.commit()

    async def run(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, team_name FROM teams")
            teams = cur.fetchall()
            
        for tid, tname in teams:
            await self.sync_team_players(tid, tname)
            await asyncio.sleep(2)

if __name__ == "__main__":
    syncer = UnderstatDeepSync()
    asyncio.run(syncer.run())
