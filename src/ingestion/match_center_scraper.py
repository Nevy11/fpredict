import os
import asyncio
import pandas as pd
import psycopg2
import json
import re
from src.ingestion.browser_scraper import BrowserScraper
from src.parsing.understat_parser import UnderstatParser
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class MatchCenterScraper:
    def __init__(self):
        self.scraper = BrowserScraper()
        self.parser = UnderstatParser()
        self.conn = psycopg2.connect(LOCAL_DB_URL)
        self.team_id_map = {} # team_name -> uuid

    def get_team_id(self, team_name):
        if team_name in self.team_id_map:
            return self.team_id_map[team_name]
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM teams WHERE team_name = %s", (team_name,))
            res = cur.fetchone()
            if res:
                self.team_id_map[team_name] = res[0]
                return res[0]
        return None

    async def get_match_list(self, year="2024"):
        url = f"https://understat.com/league/EPL/{year}"
        print(f"Fetching matches for {year} from {url}...")
        html = await self.scraper.get_raw_data(url)
        if not html: return []
        
        # Search for datesData in the scripts
        pattern = re.compile(r"JSON\.parse\(['\"](.+?)['\"]\)")
        matches = pattern.findall(html)
        for m in matches:
            decoded = bytes(m, "utf-8").decode("unicode_escape")
            if 'datesData' in decoded:
                return json.loads(decoded)
        return []

    async def ingest_match_performance(self, understat_match_id, match_date, h_name, a_name):
        url = f"https://understat.com/match/{understat_match_id}"
        html = await self.scraper.get_raw_data(url)
        if not html: return

        # Extract playersData JSON
        pattern = re.compile(r"playersData\s+=\s+JSON\.parse\(['\"](.+?)['\"]\)")
        m = pattern.search(html)
        if not m:
            print(f"Could not find playersData for match {understat_match_id}")
            return
            
        data = json.loads(bytes(m.group(1), "utf-8").decode("unicode_escape"))
        
        # Find internal match ID
        h_id = self.get_team_id(h_name)
        a_id = self.get_team_id(a_name)
        
        with self.conn.cursor() as cur:
            # 1. Update match_record with understat_id
            cur.execute(
                "UPDATE match_records SET understat_id = %s WHERE match_date = %s AND home_team_id = %s AND away_team_id = %s RETURNING id",
                (understat_match_id, match_date, h_id, a_id)
            )
            res = cur.fetchone()
            if not res:
                print(f"Could not find local match record for {h_name} vs {a_name} on {match_date}")
                return
            match_uuid = res[0]

            # 2. Ingest player stats
            # data is {'h': {id: {stats}}, 'a': {id: {stats}}}
            for side in ['h', 'a']:
                team_uuid = h_id if side == 'h' else a_id
                for u_player_id, stats in data[side].items():
                    p_name = stats['player_name']
                    
                    # Find or Create Player
                    cur.execute(
                        "INSERT INTO players (name, team_id, understat_id) VALUES (%s, %s, %s) ON CONFLICT (name, team_id) DO UPDATE SET understat_id = %s RETURNING id",
                        (p_name, team_uuid, u_player_id, u_player_id)
                    )
                    player_uuid = cur.fetchone()[0]
                    
                    # Insert Performance
                    cur.execute(
                        """INSERT INTO player_performance 
                           (player_id, match_id, minutes_played, xg_contribution, rating_score) 
                           VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                        (player_uuid, match_uuid, int(stats['time']), float(stats['xG']), float(stats['xG'])) # Using xG as rating for now
                    )
            self.conn.commit()
            print(f"Successfully ingested performance for {h_name} vs {a_name}")

    async def run_sync(self, year="2024"):
        matches = await self.get_match_list(year)
        print(f"Found {len(matches)} matches to process.")
        
        # Only process completed matches
        completed = [m for m in matches if m['isResult']]
        print(f"Processing {len(completed)} completed matches...")
        
        for m in completed:
            m_id = m['id']
            m_date = m['datetime'].split(' ')[0]
            h_name = m['h']['title']
            a_name = m['a']['title']
            await self.ingest_match_performance(m_id, m_date, h_name, a_name)
            await asyncio.sleep(1) # Be polite

if __name__ == "__main__":
    scraper = MatchCenterScraper()
    asyncio.run(scraper.run_sync("2024"))
