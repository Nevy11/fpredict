import os
import psycopg2
import asyncio
import random
from datetime import date
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from dotenv import load_dotenv

from src.models.ensemble import FPredictEngine
from src.models.simulator import FPredictSimulator
from src.models.manager_engine import ManagerPredictionEngine
from src.managers.repository import ManagerRepository

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
_manager_engine = None
_manager_repo = None

def get_manager_engine():
    global _manager_engine
    if _manager_engine is None:
        _manager_engine = ManagerPredictionEngine()
    return _manager_engine

def get_manager_repo():
    global _manager_repo
    if _manager_repo is None:
        _manager_repo = ManagerRepository()
    return _manager_repo

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

DB_TO_DISPLAY = {db: display for display, db in TEAM_NAME_MAPPING.items()}

FRONTEND_TEAMS = [
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton & Hove Albion",
    "Chelsea", "Coventry City", "Crystal Palace", "Everton", "Fulham",
    "Hull City", "Ipswich Town", "Leeds United", "Liverpool", "Manchester City",
    "Manchester United", "Newcastle United", "Nottingham Forest", "Sunderland", "Tottenham Hotspur"
]

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

from typing import List, Dict, Any

class PredictionRequest(BaseModel):
    home_team: str
    away_team: str

class PredictionResponse(BaseModel):
    home: float
    draw: float
    away: float
    odds: List[float]
    value_bets: List[Dict[str, Any]]
    home_features: Dict[str, Any]
    away_features: Dict[str, Any]
    historical_matches: List[Dict[str, Any]]

class BacktestRequest(BaseModel):
    season: str = "2023/24"
    initial_bankroll: float = 1000.0
    kelly_fraction: float = 0.5

class ManagerPredictionRequest(BaseModel):
    home_team: str
    away_team: str
    home_manager: str | None = None
    away_manager: str | None = None

def resolve_db_team_name(team_name: str) -> str:
    return TEAM_NAME_MAPPING.get(team_name, team_name)

def resolve_display_team_name(db_name: str) -> str:
    return DB_TO_DISPLAY.get(db_name, db_name)

@app.get("/teams")
def list_teams():
    return FRONTEND_TEAMS

@app.get("/features/{team_name}")
def get_feature_series(team_name: str):
    db_name = resolve_db_team_name(team_name)
    snapshots = []
    try:
        conn = psycopg2.connect(f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host=localhost")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT snapshot_date,
                       features->>'elo_rating',
                       features->>'sdi',
                       features->>'form_ppg',
                       features->>'sentiment_score',
                       features->>'squad_power'
                FROM feature_store fs
                JOIN teams t ON fs.team_id = t.id
                WHERE t.team_name = %s
                ORDER BY snapshot_date ASC
            """, (db_name,))
            rows = cur.fetchall()
            for index, row in enumerate(rows, start=1):
                snapshots.append({
                    "date": row[0].strftime("%Y-%m-%d") if hasattr(row[0], 'strftime') else str(row[0]),
                    "gameweek": f"GW{index}",
                    "elo": round(float(row[1] or 1500), 1),
                    "sdi": round(float(row[2] or 1.0), 2),
                    "form": round(float(row[3] or 1.0), 2),
                    "sentiment": round(float(row[4] or 0.0), 2),
                    "squad_power": round(float(row[5] or 0.0), 1),
                })

            cur.execute("""
                SELECT AVG((features->>'elo_rating')::float)
                FROM feature_store fs
                JOIN teams t ON fs.team_id = t.id
                WHERE t.team_name = %s
            """, (db_name,))
            avg_elo = cur.fetchone()[0] or 1500

            cur.execute("""
                SELECT AVG(
                    (1.0 / NULLIF(m.odds_home, 0)) +
                    (1.0 / NULLIF(m.odds_draw, 0)) +
                    (1.0 / NULLIF(m.odds_away, 0))
                )
                FROM match_records m
                JOIN teams th ON m.home_team_id = th.id
                WHERE th.team_name = %s AND m.odds_home IS NOT NULL
            """, (db_name,))
            overround = cur.fetchone()[0] or 1.04
        conn.close()
    except Exception as e:
        print(f"Feature series DB Error: {e}")
        raise HTTPException(status_code=500, detail="Unable to load feature store data")

    if not snapshots:
        raise HTTPException(status_code=404, detail=f"No feature data found for {team_name}")

    sentiments = [item["sentiment"] for item in snapshots]
    sentiment_range = max(sentiments) - min(sentiments) if sentiments else 0
    if sentiment_range >= 0.35:
        volatility = "High"
    elif sentiment_range >= 0.15:
        volatility = "Medium"
    else:
        volatility = "Low"

    latest = snapshots[-1]
    return {
        "team": team_name,
        "snapshots": snapshots,
        "summary": {
            "avg_elo": round(float(avg_elo), 1),
            "latest_elo": latest["elo"],
            "latest_sdi": latest["sdi"],
            "latest_form": latest["form"],
            "sentiment_volatility": volatility,
            "market_overround": round(float(overround) * 100, 1),
        },
    }

@app.post("/backtest")
def run_backtest(request: BacktestRequest):
    try:
        simulator = FPredictSimulator(initial_bankroll=request.initial_bankroll)
        report = simulator.run_backtest(
            season=request.season,
            kelly_fraction=max(0.05, min(request.kelly_fraction, 1.0)) * 0.2,
            initial_bankroll=request.initial_bankroll,
        )
        simulator.conn.close()
        return report
    except Exception as e:
        print(f"Backtest Error: {e}")
        raise HTTPException(status_code=500, detail="Backtest simulation failed")

@app.get("/managers")
def list_managers():
    repo = get_manager_repo()
    return {"managers": repo.list_manager_names()}

@app.get("/managers/lookup")
def lookup_managers(home_team: str, away_team: str):
    db_home = resolve_db_team_name(home_team)
    db_away = resolve_db_team_name(away_team)
    repo = get_manager_repo()
    try:
        return repo.lookup_match_managers(db_home, db_away)
    except Exception as error:
        print(f"Manager lookup error: {error}")
        raise HTTPException(status_code=500, detail="Unable to resolve current managers")

@app.get("/managers/{manager_name}/profile")
def get_manager_profile(manager_name: str, team: str | None = None):
    repo = get_manager_repo()
    profile = repo.get_profile(manager_name)
    if team:
        db_team = resolve_db_team_name(team)
        profile["form"] = repo.compute_manager_form(manager_name, db_team, date.today())
        profile["team"] = db_team
    return profile

@app.post("/predict/manager")
def predict_with_manager(request: ManagerPredictionRequest):
    db_home = resolve_db_team_name(request.home_team)
    db_away = resolve_db_team_name(request.away_team)
    h_features = get_team_features(request.home_team)
    a_features = get_team_features(request.away_team)
    odds = get_match_odds(request.home_team, request.away_team, h_features["elo"], a_features["elo"])
    history = get_historical_matches(request.home_team, request.away_team)

    try:
        manager_engine = get_manager_engine()
        result = manager_engine.predict(
            db_home,
            db_away,
            h_features,
            a_features,
            odds,
            home_manager_name=request.home_manager,
            away_manager_name=request.away_manager,
        )
    except Exception as error:
        print(f"Manager prediction error: {error}")
        raise HTTPException(status_code=500, detail="Manager prediction failed")

    return {
        **result,
        "odds": odds,
        "home_features": h_features,
        "away_features": a_features,
        "historical_matches": history,
    }

def get_historical_matches(home_name: str, away_name: str, limit: int = 5):
    db_h_name = TEAM_NAME_MAPPING.get(home_name, home_name)
    db_a_name = TEAM_NAME_MAPPING.get(away_name, away_name)
    matches = []
    try:
        conn = psycopg2.connect(f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host=localhost")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT m.match_date, th.team_name, ta.team_name, m.home_goals, m.away_goals
                FROM match_records m
                JOIN teams th ON m.home_team_id = th.id
                JOIN teams ta ON m.away_team_id = ta.id
                WHERE (th.team_name = %s AND ta.team_name = %s)
                   OR (th.team_name = %s AND ta.team_name = %s)
                ORDER BY m.match_date DESC
                LIMIT %s
            """, (db_h_name, db_a_name, db_a_name, db_h_name, limit))
            for row in cur.fetchall():
                matches.append({
                    "date": row[0].strftime("%Y-%m-%d") if hasattr(row[0], 'strftime') else str(row[0]),
                    "home_team": row[1],
                    "away_team": row[2],
                    "home_goals": row[3],
                    "away_goals": row[4]
                })
    except Exception as e:
        print(f"Historical Match DB Error: {e}")
    return matches

def get_match_odds(home_name: str, away_name: str, elo_home: float, elo_away: float):
    # 1. Try to fetch live odds from The Odds API (Reliable Source)
    odds_api_key = os.getenv("ODDS_API_KEY")
    if odds_api_key:
        try:
            import httpx
            # Fetch EPL odds
            url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={odds_api_key}&regions=uk&markets=h2h"
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                events = response.json()
                for event in events:
                    home_match = (home_name.split()[-1].lower() in event['home_team'].lower())
                    away_match = (away_name.split()[-1].lower() in event['away_team'].lower())
                    if home_match and away_match:
                        # Find Pinnacle or the first available bookmaker
                        bookmakers = event.get('bookmakers', [])
                        if bookmakers:
                            markets = bookmakers[0].get('markets', [])
                            for market in markets:
                                if market['key'] == 'h2h':
                                    outcomes = market['outcomes']
                                    # the-odds-api returns Name: Price
                                    odds_dict = {o['name']: o['price'] for o in outcomes}
                                    h_odd = odds_dict.get(event['home_team'])
                                    a_odd = odds_dict.get(event['away_team'])
                                    d_odd = odds_dict.get('Draw')
                                    if h_odd and a_odd and d_odd:
                                        print(f"[API] Successfully fetched live odds: Home {h_odd}, Draw {d_odd}, Away {a_odd}")
                                        return [float(h_odd), float(d_odd), float(a_odd)]
        except Exception as e:
            print(f"Live Odds API Error: {e}")

    # 2. Fallback to Database Historical Odds
    db_h_name = TEAM_NAME_MAPPING.get(home_name, home_name)
    db_a_name = TEAM_NAME_MAPPING.get(away_name, away_name)
    try:
        conn = psycopg2.connect(f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host=localhost")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT m.odds_home, m.odds_draw, m.odds_away
                FROM match_records m
                JOIN teams th ON m.home_team_id = th.id
                JOIN teams ta ON m.away_team_id = ta.id
                WHERE th.team_name = %s AND ta.team_name = %s
                  AND m.odds_home IS NOT NULL
                ORDER BY m.match_date DESC
                LIMIT 1
            """, (db_h_name, db_a_name))
            res = cur.fetchone()
            if res:
                return [float(res[0]), float(res[1]), float(res[2])]
    except Exception:
        pass
    
    # 3. Fallback: calculate implied odds from Elo with standard home advantage
    dr = (elo_home + 50) - elo_away
    p_home = 1 / (1 + 10 ** (-dr / 400))
    p_draw = 0.24 # Typical EPL draw probability
    p_home_adj = p_home * (1 - p_draw)
    p_away_adj = (1 - p_home) * (1 - p_draw)
    
    margin = 1.05 # Bookmaker overround
    return [
        round(1 / (p_home_adj * margin), 2),
        round(1 / (p_draw * margin), 2),
        round(1 / (p_away_adj * margin), 2)
    ]

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    h_features = get_team_features(request.home_team)
    a_features = get_team_features(request.away_team)
    
    odds = get_match_odds(request.home_team, request.away_team, h_features['elo'], a_features['elo'])
    
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
    
    recs = engine.trade_recommendation(request.home_team, request.away_team, odds[0], odds[1], odds[2], features_a_df, features_b)
    
    history = get_historical_matches(request.home_team, request.away_team)

    return {
        "away": probs[0] * 100,
        "draw": probs[1] * 100,
        "home": probs[2] * 100,
        "odds": odds,
        "value_bets": recs,
        "home_features": h_features,
        "away_features": a_features,
        "historical_matches": history
    }

@app.websocket("/ws/odds")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(random.uniform(2.0, 5.0))
            # Shift odds slightly by +/- 0.05
            shift_home = round(random.uniform(-0.05, 0.05), 2)
            shift_draw = round(random.uniform(-0.05, 0.05), 2)
            shift_away = round(random.uniform(-0.05, 0.05), 2)
            await websocket.send_json({
                "home": shift_home,
                "draw": shift_draw,
                "away": shift_away
            })
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
