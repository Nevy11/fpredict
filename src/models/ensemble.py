import torch
import xgboost as xgb
import pandas as pd
import numpy as np
from src.models.xgboost_tower import XGBoostTower
from src.models.contextual_tower import ContextualTowerTrainer, TowerB

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib

class FPredictEnsemble:
    """
    Ensemble Fusion Layer.
    Uses a Meta-Learner (Logistic Regression) to blend Tower A and Tower B.
    """
    def __init__(self, tower_a_model=None, tower_b_model=None):
        if tower_a_model:
            self.tower_a = tower_a_model
        else:
            self.tower_a = XGBoostTower()
            try: self.tower_a.load_model()
            except: self.tower_a.train()

        if tower_b_model:
            self.tower_b = tower_b_model
        else:
            self.tower_b_trainer = ContextualTowerTrainer()
            self.tower_b = self.tower_b_trainer.model
            try: self.tower_b_trainer.load_model()
            except: self.tower_b_trainer.train()

        self.meta_learner = LogisticRegression(max_iter=1000)
        try:
            self.load_meta_learner()
        except:
            print("Meta-Learner not found. Need to train ensemble.")

    def train_meta_learner(self, features_a_df, features_b_tensor, y_true):
        """
        Learns the optimal blend of A and B using historical predictions.
        """
        print("Training Ensemble Meta-Learner...")
        
        # 1. Augment Tower A features to match Tower B's augmented size
        # Features A: [h_elo, ..., a_elo, ..., odds_h, odds_d, odds_a, elo_diff, form_diff, gd_diff, sent_diff, month]
        # To flip: swap h_* and a_* columns, and swap odds_h and odds_away
        df_a = features_a_df.copy()
        df_a_flipped = df_a.copy()
        
        # Swap team columns
        h_cols = [c for c in df_a.columns if c.startswith('h_')]
        a_cols = [c for c in df_a.columns if c.startswith('a_')]
        for h_c, a_c in zip(h_cols, a_cols):
            df_a_flipped[h_c], df_a_flipped[a_c] = df_a[a_c], df_a[h_c]
            
        # Swap odds
        df_a_flipped['odds_home'], df_a_flipped['odds_away'] = df_a['odds_away'], df_a['odds_home']
        
        # Recalculate differences
        df_a_flipped['elo_diff'] = df_a_flipped['h_elo'] - df_a_flipped['a_elo']
        df_a_flipped['form_diff'] = df_a_flipped['h_form_ppg'] - df_a_flipped['a_form_ppg']
        df_a_flipped['gd_diff'] = df_a_flipped['h_form_gd'] - df_a_flipped['a_form_gd']
        df_a_flipped['sentiment_diff'] = df_a_flipped['h_sentiment'] - df_a_flipped['a_sentiment']
        
        df_a_combined = pd.concat([df_a, df_a_flipped])
        
        # 2. Get Probs
        probs_a = self.tower_a.model.predict_proba(df_a_combined)
        
        self.tower_b.eval()
        with torch.no_grad():
            logits_b = self.tower_b(features_b_tensor)
            probs_b = torch.softmax(logits_b, dim=1).numpy()
            
        # 3. Stack Probs as Meta-Features
        X_meta = np.hstack((probs_a, probs_b))
        
        self.meta_learner.fit(X_meta, y_true)
        
        preds = self.meta_learner.predict(X_meta)
        acc = accuracy_score(y_true, preds)
        print(f"Meta-Learner Training Complete. Ensemble Accuracy: {acc:.2%}")
        self.save_meta_learner()

    def predict(self, features_a, features_b):
        # 1. Get Tower A Probs
        probs_a = self.tower_a.model.predict_proba(features_a)[0]
        
        # 2. Get Tower B Probs
        self.tower_b.eval()
        with torch.no_grad():
            tensor_b = torch.tensor(features_b, dtype=torch.float32)
            logits_b = self.tower_b(tensor_b)
            probs_b = torch.softmax(logits_b, dim=1).numpy()[0]
            
        # 3. Use Meta-Learner to blend
        X_meta = np.array([np.hstack((probs_a, probs_b))])
        return self.meta_learner.predict_proba(X_meta)[0]

    def save_meta_learner(self, path="src/models/meta_learner.joblib"):
        joblib.dump(self.meta_learner, path)
        print(f"Meta-Learner saved to {path}")

    def load_meta_learner(self, path="src/models/meta_learner.joblib"):
        self.meta_learner = joblib.load(path)
        print(f"Meta-Learner loaded from {path}")

class FPredictEngine:
    """
    Final Orchestrator: From Teams to Value Bet.
    """
    def __init__(self):
        self.ensemble = FPredictEnsemble()
        self.bankroll = 1000.0 # Example starting bankroll

    def calculate_kelly(self, prob, odds):
        """
        Kelly Criterion: f* = (bp - q) / b
        b: decimal odds - 1
        p: probability of winning
        q: probability of losing (1-p)
        """
        b = odds - 1
        p = prob
        q = 1 - p
        f_star = (b * p - q) / b
        return max(0, f_star) # Never risk negative bankroll

    def trade_recommendation(self, h_name, a_name, odds_h, odds_d, odds_a, features_a, features_b):
        probs = self.ensemble.predict(features_a, features_b)
        # Probs: [Away%, Draw%, Home%]
        
        results = []
        # Check Home Win Value
        k_h = self.calculate_kelly(probs[2], odds_h)
        if k_h > 0.02: # 2% edge threshold
            results.append({"pick": h_name, "prob": probs[2], "kelly": k_h})
            
        # Check Away Win Value
        k_a = self.calculate_kelly(probs[0], odds_a)
        if k_a > 0.02:
            results.append({"pick": a_name, "prob": probs[0], "kelly": k_a})
            
        return results

if __name__ == "__main__":
    engine = FPredictEngine()
    print("FPredict Engine Online.")
