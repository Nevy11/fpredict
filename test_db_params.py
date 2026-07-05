import pandas as pd
import numpy as np
from src.models.ensemble import FPredictEngine

def run():
    engine = FPredictEngine()
    
    h_features = {'elo': 1763.27, 'power': 0.0, 'sdi': 1.0, 'form': 2.6, 'gd': 1.2, 'sent': 0.0}
    a_features = {'elo': 1754.77, 'power': 0.0, 'sdi': 1.0, 'form': 1.6, 'gd': 0.8, 'sent': 0.0}
    odds = [1.80, 3.60, 4.50]

    features_a_dict = {
        'h_elo': h_features['elo'], 'h_squad_power': h_features['power'], 'h_sdi': h_features['sdi'], 'h_form_ppg': h_features['form'], 'h_form_gd': h_features['gd'], 'h_sentiment': h_features['sent'],
        'a_elo': a_features['elo'], 'a_squad_power': a_features['power'], 'a_sdi': a_features['sdi'], 'a_form_ppg': a_features['form'], 'a_form_gd': a_features['gd'], 'a_sentiment': a_features['sent'],
        'odds_home': odds[0], 'odds_draw': odds[1], 'odds_away': odds[2],
        'elo_diff': h_features['elo'] - a_features['elo'],
        'form_diff': h_features['form'] - a_features['form'],
        'gd_diff': h_features['gd'] - a_features['gd'],
        'sentiment_diff': h_features['sent'] - a_features['sent'],
        'match_month': 9.0
    }
    features_a_df = pd.DataFrame([features_a_dict])

    features_b = [[
        h_features['elo'], h_features['power'], h_features['sdi'], h_features['form'], h_features['gd'], h_features['sent'],
        a_features['elo'], a_features['power'], a_features['sdi'], a_features['form'], a_features['gd'], a_features['sent'],
        odds[0], odds[1], odds[2], 9.0
    ]]

    probs = engine.ensemble.predict(features_a_df, features_b)
    print(f"Away: {probs[0]:.2%}, Draw: {probs[1]:.2%}, Home: {probs[2]:.2%}")
    
    print("\nTower A only:")
    probs_a = engine.ensemble.tower_a.model.predict_proba(features_a_df)[0]
    print(probs_a)
    
    print("\nTower B only:")
    import torch
    tensor_b = torch.tensor(features_b, dtype=torch.float32)
    logits_b = engine.ensemble.tower_b(tensor_b)
    probs_b = torch.softmax(logits_b, dim=1).detach().numpy()[0]
    print(probs_b)

if __name__ == "__main__":
    run()
