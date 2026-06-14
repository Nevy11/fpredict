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
        print("Generating High-Resolution Temporal Feature Store...")
        
        # 1. Fetch all matches ordered by date
        query = """
            SELECT m.*, h.team_name as h_name, a.team_name as a_name
            FROM match_records m
            JOIN teams h ON m.home_team_id = h.id
            JOIN teams a ON m.away_team_id = a.id
            ORDER BY m.match_date ASC
        """
        all_matches_df = pd.read_sql(query, self.conn)
        
        # 2. Fetch all players and their latest impact metrics (Simplified)
        query_squad = """
            SELECT p.id, p.team_id, p.is_injured, COALESCE(i.impact_score, 0.1) as impact_score
            FROM players p
            LEFT JOIN (
                SELECT DISTINCT ON (player_id) player_id, impact_score 
                FROM player_impact_metrics 
                ORDER BY player_id, snapshot_date DESC
            ) i ON p.id = i.player_id
        """
        all_squads_df = pd.read_sql(query_squad, self.conn)

        # 3. Elo Tracker (Memory only during batch)
        team_ratings = {} # team_id -> current_elo

        with self.conn.cursor() as cur:
            cur.execute("TRUNCATE feature_store")
            
            # To compute form efficiently, we pass the entire match history to the processor
            # but the processor masks it by date internally.
            
            processed_count = 0
            for _, match in all_matches_df.iterrows():
                h_id = match['home_team_id']
                a_id = match['away_team_id']
                h_name = match['h_name']
                a_name = match['a_name']
                m_date = match['match_date']
                
                # Get current Elos
                h_elo = team_ratings.get(h_id, 1500)
                a_elo = team_ratings.get(a_id, 1500)
                
                # Generate snapshots for both teams as of this match date
                h_squad = all_squads_df[all_squads_df['team_id'] == h_id]
                a_squad = all_squads_df[all_squads_df['team_id'] == a_id]
                
                # Note: In batch, we don't have per-match sentiment yet, so use 0.0
                h_features = self.processor.generate_snapshot(h_id, all_matches_df, h_squad, m_date, h_elo, 0.0)
                a_features = self.processor.generate_snapshot(a_id, all_matches_df, a_squad, m_date, a_elo, 0.0)
                
                # Store in feature_store
                for tid, feats in [(h_id, h_features), (a_id, a_features)]:
                    cur.execute(
                        "INSERT INTO feature_store (team_id, snapshot_date, features) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                        (tid, m_date, json.dumps(feats))
                    )
                
                # Update Elo ratings for next matches
                new_h_elo, new_a_elo = self.elo_calc.update_ratings(h_name, a_name, match['home_goals'], match['away_goals'])
                # We need to sync back to the team_ratings tracker (EloCalculator handles name-based, we use ID)
                team_ratings[h_id] = new_h_elo
                team_ratings[a_id] = new_a_elo
                
                processed_count += 1
                if processed_count % 500 == 0:
                    print(f"Processed {processed_count} matches...")

            self.conn.commit()
        print(f"Batch generation complete. {processed_count} matches processed.")

if __name__ == "__main__":
    generator = FeatureStoreBatchGenerator()
    generator.generate_all()
