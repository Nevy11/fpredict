import os
import json
import torch
import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.impute import SimpleImputer
from src.models.ensemble import FPredictEngine
from src.nlp.sentiment import KnowledgeExtractor

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = "fpredict_db"
# Use SQLAlchemy for pandas compatibility
DB_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost/{DB_NAME}"
engine_sqlalchemy = create_engine(DB_URI)

class FPredictEngineV2:
    def __init__(self):
        self.base_engine = FPredictEngine()
        self.knowledge_extractor = KnowledgeExtractor()
        self.conn = psycopg2.connect(f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host=localhost")
        self.imputer = SimpleImputer(strategy='mean')
        self._fit_imputer()

    def _fit_imputer(self):
        """Fit the imputer on historical data to ensure mean calculation is valid."""
        query = """
            SELECT 
                (h.features->>'elo_rating')::float as h_elo,
                (h.features->>'squad_power')::float as h_squad_power,
                (h.features->>'sdi')::float as h_sdi,
                (h.features->>'form_ppg')::float as h_form_ppg,
                (h.features->>'form_gd')::float as h_form_gd,
                (h.features->>'sentiment_score')::float as h_sentiment,
                (a.features->>'elo_rating')::float as a_elo,
                (a.features->>'squad_power')::float as a_squad_power,
                (a.features->>'sdi')::float as a_sdi,
                (a.features->>'form_ppg')::float as a_form_ppg,
                (a.features->>'form_gd')::float as a_form_gd,
                (a.features->>'sentiment_score')::float as a_sentiment,
                m.odds_home::float, m.odds_draw::float, m.odds_away::float,
                EXTRACT(MONTH FROM m.match_date)::float as match_month
            FROM match_records m
            JOIN feature_store h ON m.home_team_id = h.team_id AND m.match_date = h.snapshot_date
            JOIN feature_store a ON m.away_team_id = a.team_id AND m.match_date = a.snapshot_date
            LIMIT 500
        """
        df = pd.read_sql(query, engine_sqlalchemy)
        if not df.empty:
            df = df.fillna(0.0)
            self.imputer.fit(df)
            print("[ENGINE] Imputer fitted on historical feature columns.")
        else:
            self.imputer = SimpleImputer(strategy='constant', fill_value=0.0)

    def get_contextual_knowledge(self, h_name, a_name):
        knowledge_summary = {"h_factors": 0.0, "a_factors": 0.0}
        with self.conn.cursor() as cur:
            cur.execute("SELECT raw_text FROM unstructured_news WHERE processed = FALSE LIMIT 5")
            news = cur.fetchall()
            for (text,) in news:
                intel = self.knowledge_extractor.extract_knowledge(text)
                if intel and 'entity' in intel:
                    entity = str(intel['entity']).lower()
                    if h_name.lower() in entity:
                        print(f"[ENGINE] Applied Knowledge to Home Team ({h_name}): {intel.get('impact_score', 0)}")
                        knowledge_summary['h_factors'] += float(intel.get('impact_score', 0))
                    elif a_name.lower() in entity:
                        print(f"[ENGINE] Applied Knowledge to Away Team ({a_name}): {intel.get('impact_score', 0)}")
                        knowledge_summary['a_factors'] += float(intel.get('impact_score', 0))
        return knowledge_summary

    def fetch_features(self, match_id):
        query = """
            SELECT 
                (h.features->>'elo_rating')::float as h_elo,
                (h.features->>'squad_power')::float as h_squad_power,
                (h.features->>'sdi')::float as h_sdi,
                (h.features->>'form_ppg')::float as h_form_ppg,
                (h.features->>'form_gd')::float as h_form_gd,
                (h.features->>'sentiment_score')::float as h_sentiment,
                (a.features->>'elo_rating')::float as a_elo,
                (a.features->>'squad_power')::float as a_squad_power,
                (a.features->>'sdi')::float as a_sdi,
                (a.features->>'form_ppg')::float as a_form_ppg,
                (a.features->>'form_gd')::float as a_form_gd,
                (a.features->>'sentiment_score')::float as a_sentiment,
                m.odds_home::float, m.odds_draw::float, m.odds_away::float,
                EXTRACT(MONTH FROM m.match_date)::float as match_month
            FROM match_records m
            JOIN teams th ON m.home_team_id = th.id
            JOIN teams ta ON m.away_team_id = ta.id
            JOIN feature_store h ON m.home_team_id = h.team_id
            JOIN feature_store a ON m.away_team_id = a.team_id
            WHERE m.id = %s
            ORDER BY h.snapshot_date DESC, a.snapshot_date DESC
            LIMIT 1
        """
        df = pd.read_sql(query, engine_sqlalchemy, params=(match_id,))
        if df.empty: 
            print(f"[ENGINE] No features found for match {match_id}.")
            return None, None
        
        # Base columns list (all cols fitted by imputer)
        all_cols = ['h_elo', 'h_squad_power', 'h_sdi', 'h_form_ppg', 'h_form_gd', 'h_sentiment',
                    'a_elo', 'a_squad_power', 'a_sdi', 'a_form_ppg', 'a_form_gd', 'a_sentiment',
                    'odds_home', 'odds_draw', 'odds_away', 'match_month']
        
        # Fill NaN values to 0 before casting
        df = df.fillna(0.0)
        
        # Explicitly cast to float
        for col in all_cols:
            df[col] = df[col].astype(float)
        
        # Impute NaNs using the fitted imputer
        df[all_cols] = self.imputer.transform(df[all_cols])
        
        df['elo_diff'] = df['h_elo'] - df['a_elo']
        df['form_diff'] = df['h_form_ppg'] - df['a_form_ppg']
        df['gd_diff'] = df['h_form_gd'] - df['a_form_gd']
        df['sentiment_diff'] = df['h_sentiment'] - df['a_sentiment']
        
        # XGBoost cols as expected
        base_cols = all_cols[:15] # exclude match_month from base
        xgb_cols = base_cols + ['elo_diff', 'form_diff', 'gd_diff', 'sentiment_diff', 'match_month']
        
        return df[xgb_cols], df[all_cols].values

    def run_comprehensive_prediction(self, match_id):
        # 1. Fetch Match Details
        with self.conn.cursor() as cur:
            cur.execute("""SELECT h.team_name, a.team_name, m.odds_home FROM match_records m 
                           JOIN teams h ON m.home_team_id = h.id JOIN teams a ON m.away_team_id = a.id WHERE m.id = %s""", (match_id,))
            m = cur.fetchone()
        if not m: return None
        h_name, a_name, odds_h = m
        
        # 2. Get Knowledge Layer
        intel = self.get_contextual_knowledge(h_name, a_name)
        
        # 3. Dynamic Ensemble Prediction
        features_a, features_b = self.fetch_features(match_id)
        if features_a is None: return None
        
        probs = self.base_engine.ensemble.predict(features_a, features_b)
        
        # 4. Adjustment
        adj_home = probs[2] + intel['h_factors'] - intel['a_factors']
        adj_away = probs[0] + intel['a_factors'] - intel['h_factors']
        final_probs = {"home": max(0.01, min(0.99, adj_home)), "away": max(0.01, min(0.99, adj_away)), "draw": 0.0}
        final_probs["draw"] = max(0.01, 1.0 - (final_probs["home"] + final_probs["away"]))

        kelly = self.base_engine.calculate_kelly(final_probs['home'], odds_h) if odds_h else 0.0
        edge = (final_probs['home'] * (odds_h if odds_h else 0)) - 1.0
        narrative = f"Prediction for {h_name} vs {a_name}. "
        if intel['h_factors'] > intel['a_factors']: narrative += f"{h_name} edge."
        else: narrative += f"{a_name} edge."

        # 5. Save results
        with self.conn.cursor() as cur:
            cur.execute("""INSERT INTO predictions (match_id, win_probability, predicted_goals_home, predicted_goals_away, predicted_corners, predicted_shots, tactical_narrative, version_id, kelly_stake, edge_value)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (match_id, version_id) DO UPDATE SET 
                   win_probability = EXCLUDED.win_probability, kelly_stake = EXCLUDED.kelly_stake, edge_value = EXCLUDED.edge_value""",
                (match_id, json.dumps(final_probs), 1.5, 1.2, 10.5, 14.2, narrative, 'v3.0-quantum', float(kelly), float(edge)))
        self.conn.commit()
        return True
