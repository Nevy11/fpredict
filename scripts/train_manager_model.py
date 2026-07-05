#!/usr/bin/env python3
import asyncio

from src.ingestion.manager_history_loader import ManagerHistoryLoader
from src.models.manager_tower import ManagerTower


async def main():
    loader = ManagerHistoryLoader()
    loader.load_seed_data()
    await loader.scrape_current_managers()
    loader.close()

    tower = ManagerTower()
    tower.train()
    tower.close()
    print("Manager data download + model training complete.")


if __name__ == "__main__":
    asyncio.run(main())
