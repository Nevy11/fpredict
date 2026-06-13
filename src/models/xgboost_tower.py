import os
import pandas as pd
import xgboost as xgb
import psycopg2
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class XGBoostTower:
    """
    Tower A: Quantitative Regressor.
    Trains on historical tabular data to calculate base match probabilities.
    """
    def __init__(self):
        self.conn = psycopg2.connect(LOCAL_DB_URL)
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            objective='multi:softprob'
        )

    def load_training_data(self):
        print("Loading training data from Feature Store...")
        query = """
            SELECT 
                h.features->>'elo_rating' as h_elo,
                h.features->>'squad_power' as h_squad_power,
                h.features->>'sdi' as h_sdi,
                h.features->>'form_ppg' as h_form_ppg,
                h.features->>'sentiment_score' as h_sentiment,
                a.features->>'elo_rating' as a_elo,
                a.features->>'squad_power' as a_squad_power,
                a.features->>'sdi' as a_sdi,
                a.features->>'form_ppg' as a_form_ppg,
                a.features->>'sentiment_score' as a_sentiment,
                m.odds_home, m.odds_draw, m.odds_away,
                m.match_date,
                m.home_goals,
                m.away_goals
            FROM match_records m
            JOIN feature_store h ON m.home_team_id = h.team_id
            JOIN feature_store a ON m.away_team_id = a.team_id
            ORDER BY m.match_date ASC
        """
        df = pd.read_sql(query, self.conn)
        
        # 1. Cast features to float
        cols = ['h_elo', 'h_squad_power', 'h_sdi', 'h_form_ppg', 'h_sentiment', 'a_elo', 'a_squad_power', 'a_sdi', 'a_form_ppg', 'a_sentiment', 'odds_home', 'odds_draw', 'odds_away']
        for col in cols:
            df[col] = df[col].astype(float)
        
        # 2. Engineered Features
        df['elo_diff'] = df['h_elo'] - df['a_elo']
        df['form_diff'] = df['h_form_ppg'] - df['a_form_ppg']
        df['sentiment_diff'] = df['h_sentiment'] - df['a_sentiment']
        df['match_month'] = pd.to_datetime(df['match_date']).dt.month
        
        # 3. Create Target Label
        df['target'] = 1 
        df.loc[df['home_goals'] > df['away_goals'], 'target'] = 2
        df.loc[df['home_goals'] < df['away_goals'], 'target'] = 0
        
        feature_cols = cols + ['elo_diff', 'form_diff', 'sentiment_diff', 'match_month']
        return df[feature_cols], df['target']

    def train(self):
        X, y = self.load_training_data()
        if X.empty:
            print("No training data found.")
            return

        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y[split_idx:]
        
        # 4. Optimized Hyperparameters
        self.model = xgb.XGBClassifier(
            n_estimators=300,
            learning_rate=0.03,
            max_depth=7,
            min_child_weight=2,
            gamma=0.2,
            subsample=0.7,
            colsample_bytree=0.7,
            objective='multi:softprob',
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        preds = self.model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        print(f"XGBoost Tower A Training Complete. New Accuracy: {acc:.2%}")

    def predict_probs(self, squad_power, sdi):
        """Returns [Away%, Draw%, Home%]"""
        input_df = pd.DataFrame([[squad_power, sdi]], columns=['squad_power', 'sdi'])
        return self.model.predict_proba(input_df)[0]

if __name__ == "__main__":
    tower = XGBoostTower()
    tower.train()
