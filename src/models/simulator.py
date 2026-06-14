import pandas as pd
import torch
import os
import psycopg2
from dotenv import load_dotenv
from src.models.ensemble import FPredictEngine

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class FPredictSimulator:
    def __init__(self, initial_bankroll=1000.0):
        self.engine = FPredictEngine()
        self.bankroll = initial_bankroll
        self.history = []
        self.conn = psycopg2.connect(LOCAL_DB_URL)

    def run_backtest(self, season_year="2023"):
        print(f"Starting Dry Run Simulation for Season {season_year}...")
        
        # Load match data with features matched to the EXACT date
        query = """
            SELECT 
                m.id, m.match_date, h.team_name as h_name, a.team_name as a_name,
                m.home_goals, m.away_goals,
                m.odds_home, m.odds_draw, m.odds_away,
                (hf.features->>'elo_rating')::float as h_elo,
                (hf.features->>'squad_power')::float as h_power,
                (hf.features->>'sdi')::float as h_sdi,
                (hf.features->>'form_ppg')::float as h_form,
                (hf.features->>'form_gd')::float as h_gd,
                (hf.features->>'sentiment_score')::float as h_sentiment,
                (af.features->>'elo_rating')::float as a_elo,
                (af.features->>'squad_power')::float as a_power,
                (af.features->>'sdi')::float as a_sdi,
                (af.features->>'form_ppg')::float as a_form,
                (af.features->>'form_gd')::float as a_gd,
                (af.features->>'sentiment_score')::float as a_sentiment
            FROM match_records m
            JOIN teams h ON m.home_team_id = h.id
            JOIN teams a ON m.away_team_id = a.id
            JOIN feature_store hf ON m.home_team_id = hf.team_id AND m.match_date = hf.snapshot_date
            JOIN feature_store af ON m.away_team_id = af.team_id AND m.match_date = af.snapshot_date
            WHERE m.match_date >= '2023-08-01' AND m.match_date <= '2024-05-31'
            ORDER BY m.match_date ASC
        """
        df = pd.read_sql(query, self.conn)
        print(f"Simulating {len(df)} matches...")

        for _, row in df.iterrows():
            # 1. Prepare Base Features for Tower A
            match_date = pd.to_datetime(row['match_date'])
            
            features_a_dict = {
                'h_elo': row['h_elo'],
                'h_squad_power': row['h_power'],
                'h_sdi': row['h_sdi'],
                'h_form_ppg': row['h_form'],
                'h_form_gd': row['h_gd'],
                'h_sentiment': row['h_sentiment'],
                'a_elo': row['a_elo'],
                'a_squad_power': row['a_power'],
                'a_sdi': row['a_sdi'],
                'a_form_ppg': row['a_form'],
                'a_form_gd': row['a_gd'],
                'a_sentiment': row['a_sentiment'],
                'odds_home': row['odds_home'],
                'odds_draw': row['odds_draw'],
                'odds_away': row['odds_away'],
                'elo_diff': row['h_elo'] - row['a_elo'],
                'form_diff': row['h_form'] - row['a_form'],
                'gd_diff': row['h_gd'] - row['a_gd'],
                'sentiment_diff': row['h_sentiment'] - row['a_sentiment'],
                'match_month': float(match_date.month)
            }
            features_a_df = pd.DataFrame([features_a_dict])
            
            # 2. Prepare Base Features for Tower B (now 16 dimensions)
            features_b = [[
                row['h_elo'], row['h_power'], row['h_sdi'], row['h_form'], row['h_gd'], row['h_sentiment'],
                row['a_elo'], row['a_power'], row['a_sdi'], row['a_form'], row['a_gd'], row['a_sentiment'],
                row['odds_home'], row['odds_draw'], row['odds_away'], float(match_date.month)
            ]]
            
            # 3. Get trade recommendations
            trades = self.engine.trade_recommendation(
                row['h_name'], row['a_name'], 
                row['odds_home'], row['odds_draw'], row['odds_away'],
                features_a_df, 
                features_b
            )

            for trade in trades:
                bet_amount = self.bankroll * trade['kelly'] * 0.1 # Fractional Kelly (10% scale for safety)
                
                # Check result
                won = False
                if trade['pick'] == row['h_name'] and row['home_goals'] > row['away_goals']: won = True
                if trade['pick'] == row['a_name'] and row['away_goals'] > row['home_goals']: won = True
                
                if won:
                    odds = row['odds_home'] if trade['pick'] == row['h_name'] else row['odds_away']
                    profit = bet_amount * (odds - 1)
                    self.bankroll += profit
                else:
                    self.bankroll -= bet_amount
                
                self.history.append({
                    "date": row['match_date'],
                    "pick": trade['pick'],
                    "won": won,
                    "bankroll": self.bankroll
                })

        print(f"Simulation Complete. Final Bankroll: ${self.bankroll:.2f}")
        return self.bankroll

if __name__ == "__main__":
    sim = FPredictSimulator()
    sim.run_backtest()
