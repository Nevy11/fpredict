import asyncio
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from bs4 import BeautifulSoup
from src.ingestion.browser_scraper import BrowserScraper
from src.managers.seed_data import MANAGER_PROFILES
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SERVICE_ROLE_KEY")

async def update_current_managers():
    print("Starting Current Managers Update Job...")
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Missing Supabase credentials")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    scraper = BrowserScraper()
    
    url = "https://fbref.com/en/comps/9/Premier-League-Stats"
    html = await scraper.get_raw_data(url)
    
    if not html:
        print("Failed to fetch data from FBref")
        return
        
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {'id': 'stats_squads_standard_for'})
    if not table:
        print("Could not find squad table for manager extraction.")
        return

    rows = table.find('tbody').find_all('tr')
    data_to_upsert = []
    
    for row in rows:
        team_cell = row.find('th', {'data-stat': 'squad'})
        manager_cell = row.find('td', {'data-stat': 'manager'})
        form_cell = row.find('td', {'data-stat': 'form'})
        
        if not team_cell or not manager_cell:
            continue
            
        team_name = team_cell.text.strip()
        manager_name = manager_cell.text.strip()
        
        # Last 5 games (form)
        last_5 = []
        if form_cell:
            # Usually form elements in fbref are in a tags inside divs, or just text
            # Let's extract all letters W, D, L
            text = form_cell.text.replace(' ', '')
            last_5 = [char for char in text if char in ('W', 'D', 'L')]
            
        # Tactical style fallback
        tactical_style = "balanced"
        if manager_name in MANAGER_PROFILES:
            tactical_style = MANAGER_PROFILES[manager_name].get("tactical_style", "balanced")
        else:
            # Try partial match
            for m_name, profile in MANAGER_PROFILES.items():
                if m_name in manager_name or manager_name in m_name:
                    tactical_style = profile.get("tactical_style", "balanced")
                    break
                    
        print(f"{team_name}: {manager_name} ({tactical_style}) - Form: {last_5}")
        
        data_to_upsert.append({
            "team_name": team_name,
            "manager_name": manager_name,
            "tactical_style": tactical_style,
            "last_5_games": last_5
        })

    if data_to_upsert:
        print(f"Upserting {len(data_to_upsert)} records to Supabase 'current_managers' table...")
        response = supabase.table("current_managers").upsert(data_to_upsert, on_conflict="team_name").execute()
        print("Upsert complete.")
    else:
        print("No data to upsert.")

if __name__ == "__main__":
    asyncio.run(update_current_managers())
