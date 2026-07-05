import pandas as pd
import numpy as np
from src.models.ensemble import FPredictEngine

def predict_match(h_name, a_name, h_features, a_features, odds):
    engine = FPredictEngine()
    
    # Construct input DataFrames/Lists to match ensemble expected structure
    # h_elo, h_power, h_sdi, h_form, h_sentiment, a_elo, a_power, a_sdi, a_form, a_sentiment, odds_h, odds_d, odds_a, month
    
    features_a_dict = {
        'h_elo': h_features['elo'], 'h_squad_power': h_features['power'], 'h_sdi': h_features['sdi'], 'h_form_ppg': h_features['form'], 'h_form_gd': 0.5, 'h_sentiment': h_features['sent'],
        'a_elo': a_features['elo'], 'a_squad_power': a_features['power'], 'a_sdi': a_features['sdi'], 'a_form_ppg': a_features['form'], 'a_form_gd': 0.2, 'a_sentiment': a_features['sent'],
        'odds_home': odds[0], 'odds_draw': odds[1], 'odds_away': odds[2],
        'elo_diff': h_features['elo'] - a_features['elo'],
        'form_diff': h_features['form'] - a_features['form'],
        'gd_diff': 0.5 - 0.2,
        'sentiment_diff': h_features['sent'] - a_features['sent'],
        'match_month': 9.0
    }
    features_a_df = pd.DataFrame([features_a_dict])

    
    features_b = [[
        h_features['sdi'], h_features['sent'], a_features['sdi'], a_features['sent'],
        h_features['elo'], h_features['power'], h_features['sdi'], h_features['form'], 0.5, h_features['sent'],
        a_features['elo'], a_features['power'], a_features['sdi'], a_features['form'], 0.2, a_features['sent']
    ]]
    # wait, the loaded TowerB expects 16 inputs. Let's adjust features_b to that.
    # [h_elo, h_power, h_sdi, h_form, h_gd, h_sent, a_elo, a_power, a_sdi, a_form, a_gd, a_sent, odds_h, odds_d, odds_a, month]
    features_b = [[
        h_features['elo'], h_features['power'], h_features['sdi'], h_features['form'], 0.5, h_features['sent'],
        a_features['elo'], a_features['power'], a_features['sdi'], a_features['form'], 0.2, a_features['sent'],
        odds[0], odds[1], odds[2], 9.0
    ]]

    probs = engine.ensemble.predict(features_a_df, features_b)
    print(f"\n--- Prediction: {h_name} vs {a_name} ---")
    print(f"Away Win: {probs[0]:.2%}")
    print(f"Draw:     {probs[1]:.2%}")
    print(f"Home Win: {probs[2]:.2%}")

if __name__ == "__main__":
    # 2026/2027 EPL Season Teams with hypothetical baseline features
    epl_teams_26_27 = {
        "Arsenal": {'elo': 1715, 'power': 85.0, 'sdi': 0.95, 'form': 2.4, 'sent': 0.05},
        "Aston Villa": {'elo': 1650, 'power': 78.0, 'sdi': 0.90, 'form': 1.8, 'sent': 0.02},
        "Bournemouth": {'elo': 1590, 'power': 72.0, 'sdi': 0.85, 'form': 1.4, 'sent': 0.00},
        "Brentford": {'elo': 1595, 'power': 73.0, 'sdi': 0.88, 'form': 1.3, 'sent': -0.01},
        "Brighton & Hove Albion": {'elo': 1610, 'power': 74.0, 'sdi': 0.92, 'form': 1.5, 'sent': 0.01},
        "Chelsea": {'elo': 1670, 'power': 81.0, 'sdi': 0.85, 'form': 1.9, 'sent': -0.02},
        "Coventry City": {'elo': 1520, 'power': 65.0, 'sdi': 1.05, 'form': 2.0, 'sent': 0.08},
        "Crystal Palace": {'elo': 1600, 'power': 72.0, 'sdi': 0.90, 'form': 1.4, 'sent': 0.00},
        "Everton": {'elo': 1580, 'power': 71.0, 'sdi': 0.85, 'form': 1.2, 'sent': -0.03},
        "Fulham": {'elo': 1585, 'power': 72.0, 'sdi': 0.88, 'form': 1.3, 'sent': 0.00},
        "Hull City": {'elo': 1515, 'power': 64.0, 'sdi': 1.02, 'form': 1.9, 'sent': 0.07},
        "Ipswich Town": {'elo': 1530, 'power': 66.0, 'sdi': 1.00, 'form': 1.8, 'sent': 0.05},
        "Leeds United": {'elo': 1560, 'power': 70.0, 'sdi': 0.95, 'form': 1.6, 'sent': 0.03},
        "Liverpool": {'elo': 1705, 'power': 84.0, 'sdi': 0.90, 'form': 2.2, 'sent': 0.04},
        "Manchester City": {'elo': 1730, 'power': 86.0, 'sdi': 0.88, 'form': 2.5, 'sent': -0.01},
        "Manchester United": {'elo': 1660, 'power': 80.0, 'sdi': 0.82, 'form': 1.7, 'sent': -0.04},
        "Newcastle United": {'elo': 1680, 'power': 82.0, 'sdi': 0.92, 'form': 2.0, 'sent': 0.02},
        "Nottingham Forest": {'elo': 1575, 'power': 70.0, 'sdi': 0.86, 'form': 1.2, 'sent': -0.02},
        "Sunderland": {'elo': 1540, 'power': 68.0, 'sdi': 0.98, 'form': 1.7, 'sent': 0.06},
        "Tottenham Hotspur": {'elo': 1675, 'power': 81.0, 'sdi': 0.89, 'form': 1.9, 'sent': 0.01}
    }
    
    # Example match 1: Heavyweight Clash
    home_team_1 = "Manchester City"
    away_team_1 = "Arsenal"
    odds_1 = [1.90, 3.50, 4.00] # Hypothetical odds
    predict_match(home_team_1, away_team_1, epl_teams_26_27[home_team_1], epl_teams_26_27[away_team_1], odds_1)

    # Example match 2: Promoted vs Established
    home_team_2 = "Coventry City"
    away_team_2 = "Chelsea"
    odds_2 = [5.50, 4.20, 1.55]
    predict_match(home_team_2, away_team_2, epl_teams_26_27[home_team_2], epl_teams_26_27[away_team_2], odds_2)
