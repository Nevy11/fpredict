import pandas as pd
import json
from datetime import date

class FeatureStoreProcessor:
    """
    Computes dynamic features from raw scraped data and match records.
    """
    @staticmethod
    def compute_squad_degradation_index(squad_df, injury_list):
        """
        Calculates the SDI: (Total Squad Impact - Injured Player Impacts) / Total Squad Impact.
        """
        if squad_df.empty:
            return 0.0
            
        total_impact = squad_df['impact_score'].sum()
        if total_impact == 0:
            return 0.0
            
        injured_impact = squad_df[squad_df['player_id'].isin(injury_list)]['impact_score'].sum()
        
        return (total_impact - injured_impact) / total_impact

    def generate_daily_snapshot(self, team_id, match_data_df, player_performance_df, current_squad_df):
        """
        Aggregates metrics to produce a Dynamic State Vector.
        match_data_df: Latest match statistics.
        player_performance_df: Recent performance stats.
        current_squad_df: List of active players for this team.
        """
        # 1. Compute Base Power
        avg_player_rating = player_performance_df['rating_score'].mean()
        
        # 2. Compute SDI
        injury_list = current_squad_df[current_squad_df['is_injured'] == True]['player_id'].tolist()
        sdi = self.compute_squad_degradation_index(current_squad_df, injury_list)
        
        # 3. Aggregate into State Vector
        features = {
            "snapshot_date": str(date.today()),
            "squad_power": float(avg_player_rating),
            "sdi": float(sdi),
            "tactical_alignment": 0.95 # Placeholder for tactical blueprint integration
        }
        return features
