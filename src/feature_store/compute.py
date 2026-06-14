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
        if squad_df is None or squad_df.empty:
            return 1.0 # No degradation if squad is unknown
            
        total_impact = squad_df['impact_score'].sum()
        if total_impact == 0:
            return 1.0
            
        # Filter for injured players using the 'id' column
        injured_impact = squad_df[squad_df['id'].isin(injury_list)]['impact_score'].sum()
        
        return (total_impact - injured_impact) / total_impact

    @staticmethod
    def compute_rolling_form(team_id, match_history_df, as_of_date, window=5):
        """
        Calculates PPG and Goal Difference (GD) over the last N matches BEFORE as_of_date.
        """
        if match_history_df is None or match_history_df.empty:
            return 1.0, 0.0
            
        # Filter for matches involving team_id that occurred BEFORE the as_of_date
        # Ensure match_date is comparable
        match_history_df['match_date'] = pd.to_datetime(match_history_df['match_date']).dt.date
        as_of_date_obj = pd.to_datetime(as_of_date).date()
        
        mask = (
            ((match_history_df['home_team_id'] == team_id) | (match_history_df['away_team_id'] == team_id)) & 
            (match_history_df['match_date'] < as_of_date_obj)
        )
        team_matches = match_history_df[mask].sort_values('match_date', ascending=False).head(window)
        
        if team_matches.empty:
            return 1.0, 0.0 # Default starting form
            
        points = 0
        gd = 0
        for _, match in team_matches.iterrows():
            if match['home_team_id'] == team_id:
                gd += (match['home_goals'] - match['away_goals'])
                if match['home_goals'] > match['away_goals']: points += 3
                elif match['home_goals'] == match['away_goals']: points += 1
            else:
                gd += (match['away_goals'] - match['home_goals'])
                if match['away_goals'] > match['home_goals']: points += 3
                elif match['away_goals'] == match['home_goals']: points += 1
                
        return points / len(team_matches), gd / len(team_matches)

    def generate_snapshot(self, team_id, match_history_df, squad_df, as_of_date, elo_rating=1500, sentiment_score=0.0):
        """
        Aggregates metrics to produce a Point-in-Time Dynamic State Vector.
        """
        # 1. Compute Base Power
        squad_power = squad_df['impact_score'].sum() if squad_df is not None else 0.0
        
        # 2. Compute SDI
        sdi = 1.0
        if squad_df is not None and not squad_df.empty:
            if 'is_injured' in squad_df.columns:
                injury_list = squad_df[squad_df['is_injured'] == True]['id'].tolist()
                sdi = self.compute_squad_degradation_index(squad_df, injury_list)
        
        # 3. Compute Rolling Form (PPG and GD) as of specific date
        ppg, gd_per_game = self.compute_rolling_form(team_id, match_history_df, as_of_date)
        
        # 4. Aggregate into State Vector
        features = {
            "snapshot_date": str(as_of_date),
            "elo_rating": float(elo_rating),
            "squad_power": float(squad_power),
            "sdi": float(sdi),
            "form_ppg": float(ppg),
            "form_gd": float(gd_per_game),
            "sentiment_score": float(sentiment_score),
            "tactical_alignment": 0.95
        }
        return features
