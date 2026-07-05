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

    SEASON_WINDOWS = {
        "2023/24": ("2023-08-01", "2024-05-31"),
        "2024/25": ("2024-08-01", "2025-05-31"),
    }

    def run_backtest(self, season="2023/24", kelly_fraction=0.1, initial_bankroll=None):
        if initial_bankroll is not None:
            self.bankroll = initial_bankroll

        start_date, end_date = self.SEASON_WINDOWS.get(season, self.SEASON_WINDOWS["2023/24"])
        print(f"Starting Dry Run Simulation for Season {season}...")

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
            WHERE m.match_date >= %s AND m.match_date <= %s
              AND m.odds_home IS NOT NULL
            ORDER BY m.match_date ASC
        """
        df = pd.read_sql(query, self.conn, params=(start_date, end_date))
        print(f"Simulating {len(df)} matches...")
        starting_bankroll = self.bankroll
        self.history = []

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
                bet_amount = self.bankroll * trade['kelly'] * kelly_fraction

                won = False
                if trade['pick'] == row['h_name'] and row['home_goals'] > row['away_goals']:
                    won = True
                if trade['pick'] == row['a_name'] and row['away_goals'] > row['home_goals']:
                    won = True

                if won:
                    odds = row['odds_home'] if trade['pick'] == row['h_name'] else row['odds_away']
                    profit = bet_amount * (odds - 1)
                    self.bankroll += profit
                else:
                    self.bankroll -= bet_amount

                self.history.append({
                    "date": row['match_date'].strftime("%Y-%m-%d") if hasattr(row['match_date'], 'strftime') else str(row['match_date']),
                    "match": f"{row['h_name']} vs {row['a_name']}",
                    "pick": trade['pick'],
                    "won": won,
                    "bankroll": round(self.bankroll, 2),
                })

        print(f"Simulation Complete. Final Bankroll: ${self.bankroll:.2f}")
        return self.build_report(season, starting_bankroll)

    def build_report(self, season, starting_bankroll):
        wins = sum(1 for bet in self.history if bet['won'])
        total_bets = len(self.history)
        equity_curve = []
        seen_dates = set()
        for bet in self.history:
            if bet['date'] not in seen_dates:
                equity_curve.append({"date": bet['date'], "bankroll": bet['bankroll']})
                seen_dates.add(bet['date'])

        if not equity_curve:
            equity_curve.append({"date": "Start", "bankroll": round(starting_bankroll, 2)})

        roi = ((self.bankroll - starting_bankroll) / starting_bankroll * 100) if starting_bankroll else 0.0
        return {
            "season": season,
            "initial_bankroll": round(starting_bankroll, 2),
            "final_bankroll": round(self.bankroll, 2),
            "roi": round(roi, 2),
            "total_bets": total_bets,
            "wins": wins,
            "win_rate": round((wins / total_bets * 100) if total_bets else 0.0, 2),
            "equity_curve": equity_curve,
            "recent_bets": self.history[-8:][::-1],
        }

if __name__ == "__main__":
    sim = FPredictSimulator()
    sim.run_backtest()
