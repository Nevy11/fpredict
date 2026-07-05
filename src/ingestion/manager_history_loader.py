import asyncio
import os
from datetime import date

import httpx
import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from src.managers.seed_data import CURRENT_MANAGERS_2025, MANAGER_PROFILES, TENURE_SEED
from src.ingestion.manager_scraper import ManagerScraper

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"


class ManagerHistoryLoader:
    def __init__(self):
        self.conn = psycopg2.connect(LOCAL_DB_URL)

    def ensure_schema(self):
        migration_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "supabase", "migrations", "20260705180000_manager_schema.sql"
        )
        with open(migration_path, "r", encoding="utf-8") as handle:
            sql = handle.read()
        with self.conn.cursor() as cur:
            cur.execute(sql)
        self.conn.commit()

    def load_seed_data(self):
        self.ensure_schema()
        with self.conn.cursor() as cur:
            cur.execute("SELECT team_name, id FROM teams")
            team_ids = {name: team_id for name, team_id in cur.fetchall()}

            for manager_name, profile in MANAGER_PROFILES.items():
                cur.execute(
                    """
                    INSERT INTO managers (name, nationality, tactical_style, preferred_formation)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE
                    SET nationality = EXCLUDED.nationality,
                        tactical_style = EXCLUDED.tactical_style,
                        preferred_formation = EXCLUDED.preferred_formation
                    RETURNING id
                    """,
                    (
                        manager_name,
                        profile["nationality"],
                        profile["tactical_style"],
                        profile["formation"],
                    ),
                )

            cur.execute("UPDATE manager_tenures SET is_current = FALSE")
            cur.execute("DELETE FROM manager_tenures")

            for team_name, manager_name, start_date, end_date in TENURE_SEED:
                team_id = team_ids.get(team_name)
                if not team_id:
                    continue

                cur.execute("SELECT id FROM managers WHERE name = %s", (manager_name,))
                manager_row = cur.fetchone()
                if not manager_row:
                    continue

                is_current = end_date is None
                cur.execute(
                    """
                    INSERT INTO manager_tenures (manager_id, team_id, start_date, end_date, is_current)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (manager_row[0], team_id, start_date, end_date, is_current),
                )

                if is_current:
                    cur.execute(
                        "UPDATE teams SET manager_name = %s, tactical_style_id = %s WHERE id = %s",
                        (
                            manager_name,
                            MANAGER_PROFILES.get(manager_name, {}).get("tactical_style", "balanced"),
                            team_id,
                        ),
                    )

            for team_name, manager_name in CURRENT_MANAGERS_2025.items():
                team_id = team_ids.get(team_name)
                if not team_id:
                    continue
                cur.execute(
                    "UPDATE teams SET manager_name = %s, tactical_style_id = %s WHERE id = %s",
                    (
                        manager_name,
                        MANAGER_PROFILES.get(manager_name, {}).get("tactical_style", "balanced"),
                        team_id,
                    ),
                )

        self.conn.commit()
        print(f"Loaded {len(TENURE_SEED)} manager tenures into database.")

    async def scrape_current_managers(self):
        try:
            scraper = ManagerScraper()
            await scraper.scrape_managers()
            scraper.conn.close()
            print("Updated current managers from FBref.")
            return
        except Exception as error:
            print(f"Playwright manager scrape failed: {error}")

        try:
            headers = {"User-Agent": "Mozilla/5.0 FPredictBot/1.0"}
            async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
                response = await client.get("https://fbref.com/en/comps/9/Premier-League-Stats")
                if response.status_code != 200:
                    raise RuntimeError(f"FBref HTTP status {response.status_code}")

                soup = BeautifulSoup(response.text, "html.parser")
                table = soup.find("table", {"id": "stats_squads_standard_for"})
                if not table:
                    raise RuntimeError("Manager table not found")

                with self.conn.cursor() as cur:
                    cur.execute("SELECT team_name, id FROM teams")
                    teams = cur.fetchall()
                    for row in table.find("tbody").find_all("tr"):
                        squad = row.find("th", {"data-stat": "squad"})
                        manager_cell = row.find("td", {"data-stat": "manager"})
                        if not squad or not manager_cell:
                            continue
                        scraped_team = squad.text.strip()
                        manager_name = manager_cell.text.strip()
                        for team_name, team_id in teams:
                            if scraped_team.lower() in team_name.lower() or team_name.lower() in scraped_team.lower():
                                cur.execute(
                                    "UPDATE teams SET manager_name = %s WHERE id = %s",
                                    (manager_name, team_id),
                                )
                self.conn.commit()
                print("Updated current managers via HTTP scrape.")
        except Exception as error:
            print(f"HTTP manager scrape failed, using seed current managers: {error}")

    def close(self):
        self.conn.close()


async def main():
    loader = ManagerHistoryLoader()
    loader.load_seed_data()
    await loader.scrape_current_managers()
    loader.close()


if __name__ == "__main__":
    asyncio.run(main())
