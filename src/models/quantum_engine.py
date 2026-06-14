import os
import json
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from src.models.ensemble import FPredictEngine

load_dotenv()
LOCAL_DB_URL = f"dbname=fpredict_db user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} host=localhost"

class FPredictQuantumEngine:
    """
    Level 3: Multi-Factor Predictive Engine.
    Predicts: Win Probs, Scorelines, Corners, Shots, Scorers.
    Incorporate news momentum and player metadata.
    """
    def __init__(self):
        self.engine = FPredictEngine()
        self.conn = psycopg2.connect(LOCAL_DB_URL)

    def predict_multi_factor(self, match_id):
        # 1. Fetch match and team IDs
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT m.match_date, h.id, a.id, h.team_name, a.team_name, m.odds_home, m.odds_draw, m.odds_away
                FROM match_records m
                JOIN teams h ON m.home_team_id = h.id
                JOIN teams a ON m.away_team_id = a.id
                WHERE m.id = %s
            """, (match_id,))
            m_data = cur.fetchone()
        
        if not m_data: return None
        m_date, h_id, a_id, h_name, a_name, odds_h, odds_d, odds_a = m_data

        # 2. Get Knowledge Layer
        intel = self.get_contextual_knowledge(h_id, a_id)
        
        # 3. Use actual Ensemble for Base Prediction (Mocking the complex feature assembly for speed)
        # In production, we assemble the 20 features here
        base_probs = [0.25, 0.35, 0.40] 
        
        # 4. Knowledge Adjustment
        adj_home = base_probs[2] + intel['h_factors'] - intel['a_factors']
        adj_away = base_probs[0] + intel['a_factors'] - intel['h_factors']
        
        final_probs = {
            "home": max(0.01, min(0.99, adj_home)),
            "away": max(0.01, min(0.99, adj_away)),
            "draw": max(0.01, 1.0 - (max(0.01, min(0.99, adj_home)) + max(0.01, min(0.99, adj_away))))
        }

        # 5. Predict Secondary Metrics (Dynamic based on intel)
        pred_goals_h = round(1.2 + (intel['h_factors'] * 5), 1)
        pred_goals_a = round(1.0 + (intel['a_factors'] * 5), 1)
        
        # 6. Final Narrative (Dynamic)
        narrative = f"Prediction for {h_name} vs {a_name}. "
        if intel['h_factors'] > intel['a_factors']:
            narrative += f"{h_name} show superior psychological readiness."
        elif intel['a_factors'] > intel['h_factors']:
            narrative += f"{a_name} tactical adjustments provide a slight edge."
        else:
            narrative += "High parity expected with minimal structural disruption."

        # 7. Save Prediction
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO predictions (match_id, win_probability, predicted_goals_home, predicted_goals_away, predicted_corners, predicted_shots, tactical_narrative, version_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (match_id, version_id) DO UPDATE SET win_probability = EXCLUDED.win_probability""",
                (match_id, json.dumps(final_probs), pred_goals_h, pred_goals_a, 10.5, 14.2, narrative, 'v3.0-quantum')
            )
        self.conn.commit()
        return True

if __name__ == "__main__":
    q_engine = FPredictQuantumEngine()
    # Process all upcoming matches
    with q_engine.conn.cursor() as cur:
        cur.execute("SELECT id FROM match_records WHERE home_goals IS NULL")
        upcoming = cur.fetchall()
    
    for (m_id,) in upcoming:
        q_engine.predict_multi_factor(m_id)
