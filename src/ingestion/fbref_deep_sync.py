import os
import pandas as pd
import asyncio
from src.ingestion.browser_scraper import BrowserScraper
from src.parsing.fbref_parser import FBrefParser
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class FBrefDeepSync:
    def __init__(self):
        self.scraper = BrowserScraper()
        self.parser = FBrefParser()
        self.conn = psycopg2.connect(LOCAL_DB_URL)

    async def get_team_urls(self, season_url):
        print(f"Fetching team URLs from {season_url}...")
        html = await self.scraper.get_raw_data(season_url)
        if not html: return []
        
        # Simple extraction of squad URLs
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        squad_table = soup.find('table', {'id': 'stats_squads_standard_for'})
        if not squad_table:
            print("Could not find squad table.")
            return []
            
        links = squad_table.find_all('a', href=True)
        urls = []
        for link in links:
            if '/en/squads/' in link['href']:
                urls.append(f"https://fbref.com{link['href']}")
        return list(set(urls))

    async def sync_squad_stats(self, squad_url):
        print(f"Syncing squad stats from {squad_url}...")
        html = await self.scraper.get_raw_data(squad_url)
        if not html: return
        
        # Parse the 'Standard Stats' table (id=stats_standard)
        # We might need to handle other tables (Passing, Defense) later
        df = self.parser.parse_squad_stats(html)
        if df is None: return

        # Multi-index cleanup
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(1)

        print(f"Parsed {len(df)} players for this squad.")
        # Logic to save to players/player_performance tables...
        # For now, we'll just log success
        return df

    async def run(self):
        # 1. Get all teams for current season
        epl_2425_url = "https://fbref.com/en/comps/9/stats/Premier-League-Stats"
        team_urls = await self.get_team_urls(epl_2425_url)
        print(f"Found {len(team_urls)} teams.")
        
        # 2. Sync each team (limit to 1 for test)
        if team_urls:
            await self.sync_squad_stats(team_urls[0])

if __name__ == "__main__":
    syncer = FBrefDeepSync()
    asyncio.run(syncer.run())
