import os
import json
import torch
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from src.models.ensemble import FPredictEngine
from src.nlp.sentiment import KnowledgeExtractor

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class FPredictEngineV2:
    """
    Advanced Engine: Knowledge-Augmented Predictions.
    Integrates player metadata and real-time news synthesis.
    """
    def __init__(self):
        self.base_engine = FPredictEngine()
        self.knowledge_extractor = KnowledgeExtractor()
        self.conn = psycopg2.connect(LOCAL_DB_URL)

    def get_contextual_knowledge(self, h_id, a_id):
        """Fetches metadata and news for both teams."""
        knowledge_summary = {"h_factors": 0.0, "a_factors": 0.0, "scorers": []}
        
        with self.conn.cursor() as cur:
            # 1. Fetch Player Metadata
            for tid, side in [(h_id, 'h_factors'), (a_id, 'a_factors')]:
                cur.execute("""
                    SELECT name, mindset_score, skill_tags 
                    FROM players p 
                    JOIN player_metadata m ON p.id = m.player_id 
                    WHERE p.team_id = %s
                """, (tid,))
                players = cur.fetchall()
                for name, mindset, skills in players:
                    # Logic: Mindset directly adds to team momentum
                    knowledge_summary[side] += (float(mindset) * 0.01)
                    if 'set-pieces' in str(skills):
                        knowledge_summary[side] += 0.005 # Tactical advantage
            
            # 2. Fetch Latest News
            cur.execute("SELECT raw_text FROM unstructured_news WHERE processed = FALSE LIMIT 5")
            news = cur.fetchall()
            for (text,) in news:
                intel = self.knowledge_extractor.extract_knowledge(text)
                if intel:
                    # Apply impact score to the specific entity
                    if intel['entity'] in ['Arsenal', 'Man City']: # Placeholder team check
                        # In reality, look up team_id for the entity
                        knowledge_summary['h_factors'] += float(intel['impact_score'])

        return knowledge_summary

    def run_comprehensive_prediction(self, match_id):
        # 1. Fetch Match Details
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT m.match_date, h.team_name, a.team_name, m.home_team_id, m.away_team_id, m.odds_home, m.odds_draw, m.odds_away
                FROM match_records m
                JOIN teams h ON m.home_team_id = h.id
                JOIN teams a ON m.away_team_id = a.id
                WHERE m.id = %s
            """, (match_id,))
            m = cur.fetchone()
        
        if not m: return None
        date, h_name, a_name, h_id, a_id, odds_h, odds_d, odds_a = m
        
        # 2. Get Knowledge Layer
        intel = self.get_contextual_knowledge(h_id, a_id)
        
        # 3. Base Prediction (Two-Tower Ensemble)
        # We need to construct the features_a/b as we did in the simulator
        # For demonstration, we'll assume current snapshots
        base_probs = [0.15, 0.40, 0.45] # Away, Draw, Home
        
        # 4. Knowledge Adjustment
        # Adjust probabilities based on training intensity, mindset, etc.
        adj_home = base_probs[2] + intel['h_factors'] - intel['a_factors']
        adj_away = base_probs[0] + intel['a_factors'] - intel['h_factors']
        
        final_probs = {
            "home": max(0, min(1, adj_home)),
            "away": max(0, min(1, adj_away)),
            "draw": 1.0 - (max(0, min(1, adj_home)) + max(0, min(1, adj_away)))
        }

        # 5. Predict Secondary Metrics
        prediction = {
            "match_id": match_id,
            "win_probability": final_probs,
            "predicted_goals_home": 1.5 + intel['h_factors']*10,
            "predicted_goals_away": 1.1 + intel['a_factors']*10,
            "predicted_corners": 10.5,
            "predicted_shots": 14.2,
            "tactical_narrative": f"Match influenced by {h_name} squad mindset and set-piece readiness."
        }
        
        # 6. Save to DB
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO predictions (match_id, win_probability, predicted_goals_home, predicted_goals_away, predicted_corners, predicted_shots, tactical_narrative, version_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (match_id, version_id) DO UPDATE SET win_probability = EXCLUDED.win_probability""",
                (match_id, json.dumps(final_probs), prediction['predicted_goals_home'], prediction['predicted_goals_away'], 10.5, 14.2, prediction['tactical_narrative'], 'v2.0-knowledge')
            )
        self.conn.commit()
        return prediction

if __name__ == "__main__":
    engine = FPredictEngineV2()
    # Find one upcoming match
    with engine.conn.cursor() as cur:
        cur.execute("SELECT id FROM match_records WHERE home_goals IS NULL LIMIT 1")
        match_id = cur.fetchone()[0]
    
    result = engine.run_comprehensive_prediction(match_id)
    print(f"Prediction for upcoming match generated: {result['win_probability']}")
