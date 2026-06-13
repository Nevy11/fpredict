import pandas as pd
import json
from src.parsing.fbref_parser import FBrefParser
from src.parsing.understat_parser import UnderstatParser
from src.ingestion.pipeline import IngestionPipeline
import asyncio

class DataIngestionLoader:
    def __init__(self):
        self.pipeline = IngestionPipeline()
        self.fbref_parser = FBrefParser()
        self.understat_parser = UnderstatParser()

    async def ingest_fbref_data(self, file_path, team_id):
        # Read the downloaded CSV/HTML data
        with open(file_path, 'r') as f:
            raw_data = f.read()
        
        # Parse using the FBrefParser
        df = self.fbref_parser.parse_squad_stats(raw_data)
        
        # Ingest to DB
        if df is not None:
            await self.pipeline.ingest_to_db(f"fbref_{team_id}", df)
            print(f"Successfully ingested FBref data for {team_id}")

    async def ingest_understat_data(self, file_path, team_id):
        with open(file_path, 'r') as f:
            raw_data = f.read()
            
        data = self.understat_parser.parse_team_data(raw_data)
        
        if data:
            await self.pipeline.ingest_to_db(f"understat_{team_id}", data)
            print(f"Successfully ingested Understat data for {team_id}")

# This will serve as the integration bridge
if __name__ == "__main__":
    loader = DataIngestionLoader()
    # Example trigger for ingestion
    # asyncio.run(loader.ingest_fbref_data("data/raw/fbref_team_1.html", "team_1"))
