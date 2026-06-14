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
    # Hypothetical values based on team status
    # City (Maresca coach = lower SDI/Sentiment) vs Arsenal (Champ = Stable)
    city_features = {'elo': 1716, 'power': 85.0, 'sdi': 0.8, 'form': 2.5, 'sent': -0.03}
    ars_features = {'elo': 1709, 'power': 82.0, 'sdi': 0.95, 'form': 2.4, 'sent': 0.01}
    odds = [1.90, 3.50, 4.00] # City favorite
    
    predict_match("Man City", "Arsenal", city_features, ars_features, odds)
