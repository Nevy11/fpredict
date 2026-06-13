import os
import json
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from src.feature_store.compute import FeatureStoreProcessor
from src.feature_store.elo import EloCalculator

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class FeatureStoreBatchGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(LOCAL_DB_URL)
        self.processor = FeatureStoreProcessor()
        self.elo_calc = EloCalculator()

    def generate_all(self):
        print("Generating batch feature snapshots with real match, Elo, and Sentiment data...")
        
        # 1. Calculate Elo Ratings
        all_elo_ratings = self.elo_calc.run_historical()
        
        # 2. Fetch Latest Sentiment for each team
        with self.conn.cursor() as cur:
            cur.execute("SELECT team_id, AVG(sentiment_score) FROM unstructured_news WHERE processed = TRUE GROUP BY team_id")
            sentiment_map = dict(cur.fetchall())

        all_matches_df = pd.read_sql("SELECT * FROM match_records", self.conn)
        # Load real squad data
        all_squads_df = pd.read_sql("SELECT * FROM players", self.conn)
        all_squads_df['impact_score'] = 0.1 # Default impact

        with self.conn.cursor() as cur:
            cur.execute("TRUNCATE feature_store")
            cur.execute("SELECT id, team_name FROM teams")
            teams = cur.fetchall()
            
            for team_id, team_name in teams:
                print(f"Processing features for {team_name}...")
                elo = all_elo_ratings.get(team_name, 1500)
                sentiment = sentiment_map.get(team_id, 0.0)
                team_squad = all_squads_df[all_squads_df['team_id'] == team_id]
                
                features = self.processor.generate_daily_snapshot(
                    team_id, all_matches_df, None, team_squad, elo_rating=elo, sentiment_score=sentiment
                )
                
                cur.execute(
                    "INSERT INTO feature_store (team_id, snapshot_date, features) VALUES (%s, %s, %s)",
                    (team_id, features['snapshot_date'], json.dumps(features))
                )
            self.conn.commit()
        print("Batch generation complete.")

if __name__ == "__main__":
    generator = FeatureStoreBatchGenerator()
    generator.generate_all()
