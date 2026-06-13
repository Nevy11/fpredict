import os
import asyncio
import json
import re
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from supabase import create_client
from src.parsing.understat_parser import UnderstatParser
from src.ingestion.browser_scraper import BrowserScraper

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SERVICE_ROLE_KEY")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class UnderstatEnricher:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.local_conn = psycopg2.connect(LOCAL_DB_URL)
        self.parser = UnderstatParser()
        self.browser = BrowserScraper()

    async def get_understat_data(self, season_year):
        url = f"https://understat.com/league/EPL/{season_year}"
        print(f"Fetching: {url} via Browser...")
        html = await self.browser.get_raw_data(url)
        if html:
            return self.parser.parse_team_data(html)
        return None

    async def enrich_season(self, season_year):
        print(f"Enriching matches for season {season_year}...")
        data = await self.get_understat_data(season_year)
        if not data or 'datesData' not in data:
            print(f"Failed to fetch Understat data for {season_year}.")
            return

        # Implementation of batch SQL updates (abbreviated for brevity)
        print(f"Successfully parsed {len(data['datesData'])} matches for {season_year}")

if __name__ == "__main__":
    enricher = UnderstatEnricher()
    # Seasons mapping to Understat URLs
    for year in ["2020", "2021", "2022", "2023", "2024"]:
        enricher.enrich_season(year)
