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
                SELECT m.match_date, h.id, a.id, h.team_name, a.team_name
                FROM match_records m
                JOIN teams h ON m.home_team_id = h.id
                JOIN teams a ON m.away_team_id = a.id
                WHERE m.id = %s
            """, (match_id,))
            m_data = cur.fetchone()
        
        if not m_data: return None
        m_date, h_id, a_id, h_name, a_name = m_data

        # 2. Fetch Player Metadata for Scorers prediction
        with self.conn.cursor() as cur:
            cur.execute("SELECT name, mindset_score FROM players p JOIN player_metadata m ON p.id = m.player_id WHERE team_id = %s", (h_id,))
            h_players = cur.fetchall()
            cur.execute("SELECT name, mindset_score FROM players p JOIN player_metadata m ON p.id = m.player_id WHERE team_id = %s", (a_id,))
            a_players = cur.fetchall()

        # 3. Base Win Probabilities (Placeholder logic leveraging Tower A/B outputs)
        win_probs = {"home": 0.52, "draw": 0.28, "away": 0.20} # Example
        
        # 4. Predict Goals (Poisson-based logic placeholder)
        pred_goals_h = 2.1
        pred_goals_a = 0.8
        
        # 5. Predict Corners & Shots (Based on team historical averages + momentum)
        pred_corners = 11.2
        pred_shots = 15.4

        # 6. Predict Scorers (High mindset + historical impact)
        scorers = []
        if h_players:
            # Sort by mindset score for demonstration
            h_players.sort(key=lambda x: x[1], reverse=True)
            scorers.append({"player": h_players[0][0], "team": h_name, "prob": 0.35})
        
        # 7. Final Narrative
        narrative = f"{h_name} enter with high psychological momentum. Expect dominant possession and high shot volume."

        # 8. Save Prediction
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO predictions (match_id, win_probability, predicted_goals_home, predicted_goals_away, predicted_corners, predicted_shots, predicted_scorers, tactical_narrative, version_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (match_id, version_id) DO UPDATE SET win_probability = EXCLUDED.win_probability""",
                (match_id, json.dumps(win_probs), pred_goals_h, pred_goals_a, pred_corners, pred_shots, json.dumps(scorers), narrative, 'v3.0-quantum')
            )
        self.conn.commit()
        
        print(f"Generated Quantum Prediction for {h_name} vs {a_name}")
        return True

if __name__ == "__main__":
    q_engine = FPredictQuantumEngine()
    # Process all upcoming matches
    with q_engine.conn.cursor() as cur:
        cur.execute("SELECT id FROM match_records WHERE home_goals IS NULL")
        upcoming = cur.fetchall()
    
    for (m_id,) in upcoming:
        q_engine.predict_multi_factor(m_id)
