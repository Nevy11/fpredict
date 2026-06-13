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
            
        injured_impact = squad_df[squad_df['id'].isin(injury_list)]['impact_score'].sum()
        
        return (total_impact - injured_impact) / total_impact

    @staticmethod
    def compute_rolling_form(team_id, match_history_df, window=5):
        """
        Calculates average goals/results over the last N matches.
        """
        if match_history_df.empty:
            return 0.0
            
        # Sort by date and filter for matches involving team_id
        team_matches = match_history_df[
            (match_history_df['home_team_id'] == team_id) | 
            (match_history_df['away_team_id'] == team_id)
        ].sort_values('match_date', ascending=False).head(window)
        
        if team_matches.empty:
            return 0.0
            
        # Simplified form: Points per game over window
        points = 0
        for _, match in team_matches.iterrows():
            if match['home_team_id'] == team_id:
                if match['home_goals'] > match['away_goals']: points += 3
                elif match['home_goals'] == match['away_goals']: points += 1
            else:
                if match['away_goals'] > match['home_goals']: points += 3
                elif match['away_goals'] == match['home_goals']: points += 1
                
        return points / len(team_matches)

    def generate_daily_snapshot(self, team_id, match_data_df, player_performance_df, current_squad_df, elo_rating=1500, sentiment_score=0.0):
        """
        Aggregates metrics to produce a Dynamic State Vector.
        """
        # 1. Compute Base Power
        avg_player_rating = player_performance_df['rating_score'].mean() if player_performance_df is not None else 6.5
        
        # 2. Compute SDI
        sdi = 1.0
        if current_squad_df is not None and not current_squad_df.empty:
            # Check if 'is_injured' column exists
            if 'is_injured' in current_squad_df.columns:
                injury_list = current_squad_df[current_squad_df['is_injured'] == True]['id'].tolist()
                sdi = self.compute_squad_degradation_index(current_squad_df, injury_list)
        
        # 3. Compute Rolling Form
        form = self.compute_rolling_form(team_id, match_data_df) if match_data_df is not None else 1.0
        
        # 4. Aggregate into State Vector
        features = {
            "snapshot_date": str(date.today()),
            "elo_rating": float(elo_rating),
            "squad_power": float(avg_player_rating),
            "sdi": float(sdi),
            "form_ppg": float(form),
            "sentiment_score": float(sentiment_score),
            "tactical_alignment": 0.95
        }
        return features
