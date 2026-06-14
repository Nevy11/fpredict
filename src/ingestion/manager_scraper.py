import os
import pandas as pd
import asyncio
from src.ingestion.browser_scraper import BrowserScraper
import psycopg2
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class ManagerScraper:
    def __init__(self):
        self.scraper = BrowserScraper()
        self.conn = psycopg2.connect(LOCAL_DB_URL)

    async def scrape_managers(self):
        # FBref Premier League 2024-25 Season Summary page contains the manager names
        url = "https://fbref.com/en/comps/9/Premier-League-Stats"
        print(f"Scraping current managers from {url}...")
        
        html = await self.scraper.get_raw_data(url)
        if not html: return

        soup = BeautifulSoup(html, 'html.parser')
        # The squad table has a 'Manager' column
        table = soup.find('table', {'id': 'stats_squads_standard_for'})
        if not table:
            print("Could not find squad table for manager extraction.")
            return

        with self.conn.cursor() as cur:
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                team_name = row.find('th', {'data-stat': 'squad'}).text.strip()
                manager_name = row.find('td', {'data-stat': 'manager'}).text.strip()
                
                print(f"Team: {team_name} -> Manager: {manager_name}")
                
                # Update DB
                cur.execute(
                    "UPDATE teams SET manager_name = %s WHERE team_name ILIKE %s",
                    (manager_name, f"%{team_name}%")
                )
            self.conn.commit()
        print("Manager population complete.")

if __name__ == "__main__":
    asyncio.run(ManagerScraper().scrape_managers())
