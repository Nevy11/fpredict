import psycopg2
import pandas as pd
import torch
import os
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class LineupDatasetBuilder:
    def __init__(self):
        self.conn = psycopg2.connect(LOCAL_DB_URL)
        
    def get_match_lineup(self, match_id, team_id):
        """
        Fetch the 11 starting players and their stats for a given match and team.
        """
        query = """
            SELECT 
                p.id as player_id,
                COALESCE(ps.minutes_played, 0) as minutes_played,
                COALESCE(ps.xg_contribution, 0.0) as xg_contribution,
                COALESCE(ps.progressive_passes, 0) as progressive_passes,
                COALESCE(ps.pressing_regains, 0) as pressing_regains,
                COALESCE(ps.rating_score, 0.0) as rating_score
            FROM player_performance ps
            JOIN players p ON p.id = ps.player_id
            WHERE ps.match_id = %s AND p.team_id = %s
            ORDER BY ps.minutes_played DESC
            LIMIT 11;
        """
        return pd.read_sql(query, self.conn, params=(match_id, team_id))

    def build_dataset(self, num_player_features=5, num_manager_features=3):
        """
        Builds the PyTorch TensorDataset from the PostgreSQL database.
        """
        import sys
        import os
        # Add the root 'fpredict' directory to path so 'src.*' imports work
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from src.managers.repository import ManagerRepository
        
        manager_repo = ManagerRepository()
        
        print("Fetching matches from database...")
        matches_query = """
            SELECT 
                m.id as match_id, 
                m.match_date,
                m.home_team_id, 
                m.away_team_id, 
                th.team_name as home_team_name,
                ta.team_name as away_team_name,
                m.home_goals, 
                m.away_goals
            FROM match_records m
            JOIN teams th ON th.id = m.home_team_id
            JOIN teams ta ON ta.id = m.away_team_id
            WHERE m.home_goals IS NOT NULL
            ORDER BY m.match_date DESC
            LIMIT 1000;
        """
        matches_df = pd.read_sql(matches_query, self.conn)
        
        home_players_list, away_players_list = [], []
        home_mgr_list, away_mgr_list = [], []
        match_targets = []
        
        # Player target stats (for multi-task learning)
        home_players_targets_list, away_players_targets_list = [], []

        for _, match in matches_df.iterrows():
            m_id = match['match_id']
            h_id = match['home_team_id']
            a_id = match['away_team_id']
            
            h_name = match['home_team_name']
            a_name = match['away_team_name']
            
            # Fetch Lineups
            h_lineup = self.get_match_lineup(m_id, h_id)
            a_lineup = self.get_match_lineup(m_id, a_id)
            
            # Skip if we don't have exactly 11 players recorded
            if len(h_lineup) != 11 or len(a_lineup) != 11:
                continue
                
            # Fetch Managers via ManagerRepository (uses historical data if available, fallback to current)
            try:
                # build_feature_vector calculates things like h_mgr_ppg, a_mgr_ppg, mgr_ppg_diff
                mgr_feats = manager_repo.build_feature_vector(h_name, a_name, match_date=match['match_date'])
                
                # Split the features back to home and away components
                h_mgr_tensor = torch.tensor([mgr_feats.get('h_mgr_ppg', 0.0), 
                                             mgr_feats.get('h_mgr_win_rate', 0.0), 
                                             mgr_feats.get('h_mgr_style', 0.0)], dtype=torch.float32)
                
                a_mgr_tensor = torch.tensor([mgr_feats.get('a_mgr_ppg', 0.0), 
                                             mgr_feats.get('a_mgr_win_rate', 0.0), 
                                             mgr_feats.get('a_mgr_style', 0.0)], dtype=torch.float32)
            except Exception:
                h_mgr_tensor = torch.zeros(num_manager_features)
                a_mgr_tensor = torch.zeros(num_manager_features)
            
            # Player tensors
            feature_cols = ['minutes_played', 'xg_contribution', 'progressive_passes', 'pressing_regains', 'rating_score']
            h_tensor = torch.tensor(h_lineup[feature_cols].values, dtype=torch.float32)
            a_tensor = torch.tensor(a_lineup[feature_cols].values, dtype=torch.float32)
            
            home_players_list.append(h_tensor)
            away_players_list.append(a_tensor)
            home_players_targets_list.append(h_tensor) 
            away_players_targets_list.append(a_tensor) 
            
            home_mgr_list.append(h_mgr_tensor)
            away_mgr_list.append(a_mgr_tensor)
            
            # Match Target (0: Away, 1: Draw, 2: Home)
            if match['home_goals'] > match['away_goals']:
                match_targets.append(2)
            elif match['home_goals'] < match['away_goals']:
                match_targets.append(0)
            else:
                match_targets.append(1)

        print(f"Successfully processed {len(match_targets)} matches with complete 11v11 data.")
        
        # Close the manager repo connection
        manager_repo.close()
        
        # Stack into final batched tensors
        return torch.utils.data.TensorDataset(
            torch.stack(home_players_list),
            torch.stack(away_players_list),
            torch.stack(home_mgr_list),
            torch.stack(away_mgr_list),
            torch.stack(home_players_targets_list),
            torch.stack(away_players_targets_list),
            torch.tensor(match_targets, dtype=torch.long)
        )

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    builder = LineupDatasetBuilder()
    try:
        dataset = builder.build_dataset()
        print(f"Dataset ready. Size: {len(dataset)}")
    except Exception as e:
        print(f"Ensure your DB tables (player_match_stats, manager_history, match_records) exist. Error: {e}")
    finally:
        builder.close()
