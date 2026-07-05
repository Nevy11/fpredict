from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from src.models.ensemble import FPredictEngine

app = FastAPI(title="FPredict API")

# Setup CORS to allow requests from the web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load engine globally so it's not reloaded on every request
engine = FPredictEngine()

# 2026/2027 EPL Season Teams with hypothetical baseline features
EPL_TEAMS_26_27 = {
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

class PredictionRequest(BaseModel):
    home_team: str
    away_team: str

class PredictionResponse(BaseModel):
    home: float
    draw: float
    away: float

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    if request.home_team not in EPL_TEAMS_26_27 or request.away_team not in EPL_TEAMS_26_27:
        raise HTTPException(status_code=400, detail="Team not found")
        
    h_features = EPL_TEAMS_26_27[request.home_team]
    a_features = EPL_TEAMS_26_27[request.away_team]
    
    # Simple mocked odds for now
    odds = [2.00, 3.20, 3.50]
    
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
        h_features['elo'], h_features['power'], h_features['sdi'], h_features['form'], 0.5, h_features['sent'],
        a_features['elo'], a_features['power'], a_features['sdi'], a_features['form'], 0.2, a_features['sent'],
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
