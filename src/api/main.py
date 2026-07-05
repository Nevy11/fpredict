import os
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from dotenv import load_dotenv

from src.models.ensemble import FPredictEngine

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = "fpredict_db"

app = FastAPI(title="FPredict API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = FPredictEngine()

TEAM_NAME_MAPPING = {
    "Brighton & Hove Albion": "Brighton",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
    "Leicester City": "Leicester",
    "Leeds United": "Leeds",
    "Coventry City": "Coventry"
}

# Fallback hypothetical baseline
FALLBACK_FEATURES = {
    'elo': 1500, 'power': 70.0, 'sdi': 1.0, 'form': 1.0, 'sent': 0.0, 'gd': 0.0
}

def get_team_features(team_name: str):
    db_name = TEAM_NAME_MAPPING.get(team_name, team_name)
    try:
        conn = psycopg2.connect(f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host=localhost")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT f.features 
                FROM teams t 
                JOIN feature_store f ON t.id = f.team_id 
                WHERE t.team_name = %s 
                ORDER BY f.snapshot_date DESC 
                LIMIT 1
            """, (db_name,))
            res = cur.fetchone()
            if res and res[0]:
                features = res[0]
                return {
                    'elo': float(features.get('elo_rating', 1500)),
                    'power': float(features.get('squad_power', 70.0)),
                    'sdi': float(features.get('sdi', 1.0)),
                    'form': float(features.get('form_ppg', 1.0)),
                    'sent': float(features.get('sentiment_score', 0.0)),
                    'gd': float(features.get('form_gd', 0.0))
                }
    except Exception as e:
        print(f"DB Error: {e}")
    return dict(FALLBACK_FEATURES)

class PredictionRequest(BaseModel):
    home_team: str
    away_team: str

class PredictionResponse(BaseModel):
    home: float
    draw: float
    away: float

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    h_features = get_team_features(request.home_team)
    a_features = get_team_features(request.away_team)
    
    # In a fully live environment, odds would be fetched dynamically. Using baselines for now.
    odds = [2.00, 3.20, 3.50]
    
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
    
    return {
        "away": probs[0] * 100,
        "draw": probs[1] * 100,
        "home": probs[2] * 100
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
