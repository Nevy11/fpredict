import os
import torch
import psycopg2
import pandas as pd
from datetime import date

from src.models.lineup_match_model import LineupMatchModel
from src.managers.repository import ManagerRepository
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class LineupEngine:
    def __init__(self):
        self.model = LineupMatchModel(
            num_player_features=5, 
            num_manager_features=3, 
            hidden_dim=64, 
            num_player_outputs=5, 
            num_match_outputs=3
        )
        model_path = os.path.join(os.path.dirname(__file__), "lineup_match_model.pth")
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path))
            self.model.eval()
            self.is_ready = True
        else:
            self.is_ready = False
            
        self.manager_repo = ManagerRepository()

    def get_top_11_players(self, team_name):
        conn = psycopg2.connect(LOCAL_DB_URL)
        query = """
            SELECT 
                p.id as player_id,
                p.name as player_name,
                COALESCE(pim.impact_score, 0.0) as rating_score,
                0.0 as xg_contribution,
                0.0 as progressive_passes,
                0.0 as pressing_regains,
                0.0 as minutes_played
            FROM players p
            JOIN teams t ON t.id = p.team_id
            LEFT JOIN LATERAL (
                SELECT impact_score 
                FROM player_impact_metrics 
                WHERE player_id = p.id
                ORDER BY snapshot_date DESC LIMIT 1
            ) pim ON true
            WHERE t.team_name = %s
            ORDER BY pim.impact_score DESC NULLS LAST
            LIMIT 11;
        """
        df = pd.read_sql(query, conn, params=(team_name,))
        conn.close()
        return df

    def predict(self, home_team: str, away_team: str):
        if not self.is_ready:
            return None
            
        h_df = self.get_top_11_players(home_team)
        a_df = self.get_top_11_players(away_team)
        
        if len(h_df) < 11 or len(a_df) < 11:
            return None # Not enough players mapped
            
        # Manager Features
        mgr_feats = self.manager_repo.build_feature_vector(home_team, away_team, match_date=date.today())
        h_mgr_tensor = torch.tensor([[mgr_feats.get('h_mgr_ppg', 0.0), mgr_feats.get('h_mgr_win_rate', 0.0), mgr_feats.get('h_mgr_style', 0.0)]], dtype=torch.float32)
        a_mgr_tensor = torch.tensor([[mgr_feats.get('a_mgr_ppg', 0.0), mgr_feats.get('a_mgr_win_rate', 0.0), mgr_feats.get('a_mgr_style', 0.0)]], dtype=torch.float32)

        feature_cols = ['minutes_played', 'xg_contribution', 'progressive_passes', 'pressing_regains', 'rating_score']
        h_tensor = torch.tensor([h_df[feature_cols].values], dtype=torch.float32)
        a_tensor = torch.tensor([a_df[feature_cols].values], dtype=torch.float32)
        
        with torch.no_grad():
            match_preds, h_player_preds, a_player_preds = self.model(h_tensor, a_tensor, h_mgr_tensor, a_mgr_tensor)
            
        # Softmax match preds
        match_probs = torch.nn.functional.softmax(match_preds, dim=1).numpy()[0]
        
        # Format Player Predictions (top 2 players for UI)
        def format_players(df, preds):
            players = []
            for i in range(min(2, len(df))): # Take top 2 for the UI mock replacement
                # Output map: minutes_played, xg_contribution, progressive_passes, pressing_regains, rating_score
                pred = preds[0][i].numpy()
                players.append({
                    "name": df.iloc[i]['player_name'],
                    "predicted_rating": round(float(pred[4]), 1),
                    "stats": {
                        "minutes_played": max(0, int(pred[0])),
                        "xg_contribution": round(float(pred[1]), 2),
                        "progressive_passes": max(0, int(pred[2])),
                        "pressing_regains": max(0, int(pred[3])),
                    }
                })
            return players

        return {
            "match_probs": {
                "away": float(match_probs[0] * 100),
                "draw": float(match_probs[1] * 100),
                "home": float(match_probs[2] * 100)
            },
            "player_predictions": {
                "home": format_players(h_df, h_player_preds),
                "away": format_players(a_df, a_player_preds)
            }
        }
