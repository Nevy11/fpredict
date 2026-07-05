import pandas as pd
from src.api.main import get_team_features, get_match_odds
from src.models.ensemble import FPredictEngine

engine = FPredictEngine()

h_features = get_team_features("Manchester City")
a_features = get_team_features("Arsenal")
odds = get_match_odds("Manchester City", "Arsenal", h_features['elo'], a_features['elo'])

print("Home Features:", h_features)
print("Away Features:", a_features)
print("Odds:", odds)

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

print("Features A DF:")
print(features_a_df.to_dict())

print("Features B:")
print(features_b)

probs_a = engine.ensemble.tower_a.model.predict_proba(features_a_df)[0]
print("Tower A Probs:", probs_a)

import torch
engine.ensemble.tower_b.eval()
with torch.no_grad():
    tensor_b = torch.tensor(features_b, dtype=torch.float32)
    logits_b = engine.ensemble.tower_b(tensor_b)
    probs_b = torch.softmax(logits_b, dim=1).numpy()[0]
print("Tower B Probs:", probs_b)

probs = engine.ensemble.predict(features_a_df, features_b)
print("Ensemble Probs:", probs)
