import os
import asyncio
import psycopg2
from dotenv import load_dotenv
from src.ingestion.pipeline import IngestionPipeline
from src.nlp.manager import NLPManager
from src.feature_store.batch_generate import FeatureStoreBatchGenerator
from src.models.ensemble import FPredictEngine

load_dotenv()

class PipelineMaster:
    """
    The Friday Night Orchestrator.
    Automates news scraping, feature generation, and trading signals.
    """
    def __init__(self):
        self.ingestion = IngestionPipeline()
        self.nlp = NLPManager()
        self.feature_store = FeatureStoreBatchGenerator()
        self.engine = FPredictEngine()

    async def run_weekend_workflow(self):
        print("--- INITIATING WEEKEND WORKFLOW ---")
        
        # 1. Scrape latest news (Placeholder URL - in reality you'd have a list)
        print("\nStep 1: Ingesting latest news...")
        # await self.ingestion.run("https://www.bbc.com/sport/football/premier-league")
        
        # 2. Process News for Sentiment
        print("\nStep 2: Processing sentiment scoring...")
        self.nlp.process_unprocessed_news_local()
        
        # 3. Refresh Feature Store
        print("\nStep 3: Refreshing Dynamic State Vectors...")
        self.feature_store.generate_all()
        
        # 4. Generate Trading Signals for upcoming matches
        print("\nStep 4: Identifying Value Bets...")
        # Logic to fetch upcoming fixtures from DB and run predictions
        # (Assuming upcoming fixtures are ingested into match_records with null goals)
        print("Scanning upcoming fixtures for edge...")
        
        print("\n--- WORKFLOW COMPLETE ---")

if __name__ == "__main__":
    master = PipelineMaster()
    asyncio.run(master.run_weekend_workflow())
