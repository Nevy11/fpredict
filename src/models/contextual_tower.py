import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv()
LOCAL_DB_URL = f"dbname=fpredict_db user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} host=localhost"

class TowerB(nn.Module):
    """
    Tower B: Contextual Deep Neural Network (DNN).
    """
    def __init__(self, input_size=16, hidden_dims=[64, 128, 128, 64, 32]):
        super(TowerB, self).__init__()
        
        layers = []
        current_dim = input_size
        
        for h_dim in hidden_dims:
            lin = nn.Linear(current_dim, h_dim)
            nn.init.xavier_uniform_(lin.weight)
            layers.append(lin)
            layers.append(nn.BatchNorm1d(h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.3))
            current_dim = h_dim
            
        self.feature_extractor = nn.Sequential(*layers)
        self.output_layer = nn.Linear(current_dim, 3)

    def forward(self, x):
        features = self.feature_extractor(x)
        return self.output_layer(features)

class ContextualTowerTrainer:
    def __init__(self):
        self.conn = psycopg2.connect(LOCAL_DB_URL)
        self.model = TowerB()
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.005, weight_decay=1e-5)
        self.scheduler = optim.lr_scheduler.ExponentialLR(self.optimizer, gamma=0.95)

    def load_data(self):
        print("Loading high-resolution contextual data for Tower B...")
        query = """
            SELECT 
                (h.features->>'elo_rating')::float as h_elo,
                (h.features->>'squad_power')::float as h_power,
                (h.features->>'sdi')::float as h_sdi,
                (h.features->>'form_ppg')::float as h_form,
                (h.features->>'form_gd')::float as h_gd,
                (h.features->>'sentiment_score')::float as h_sentiment,
                (a.features->>'elo_rating')::float as a_elo,
                (a.features->>'squad_power')::float as a_power,
                (a.features->>'sdi')::float as a_sdi,
                (a.features->>'form_ppg')::float as a_form,
                (a.features->>'form_gd')::float as a_gd,
                (a.features->>'sentiment_score')::float as a_sentiment,
                m.odds_home::float, m.odds_draw::float, m.odds_away::float,
                EXTRACT(MONTH FROM m.match_date)::float as match_month,
                m.home_goals, m.away_goals
            FROM match_records m
            JOIN feature_store h ON m.home_team_id = h.team_id AND m.match_date = h.snapshot_date
            JOIN feature_store a ON m.away_team_id = a.team_id AND m.match_date = a.snapshot_date
            ORDER BY m.match_date ASC
        """
        df = pd.read_sql(query, self.conn)
        
        cols = ['h_elo', 'h_power', 'h_sdi', 'h_form', 'h_gd', 'h_sentiment', 
                'a_elo', 'a_power', 'a_sdi', 'a_form', 'a_gd', 'a_sentiment', 
                'odds_home', 'odds_draw', 'odds_away', 'match_month']
        
        X = df[cols].values
        y = []
        for _, row in df.iterrows():
            if row['home_goals'] > row['away_goals']: y.append(2)
            elif row['home_goals'] == row['away_goals']: y.append(1)
            else: y.append(0)
            
        X_flipped = df[['a_elo', 'a_power', 'a_sdi', 'a_form', 'a_gd', 'a_sentiment',
                        'h_elo', 'h_power', 'h_sdi', 'h_form', 'h_gd', 'h_sentiment',
                        'odds_away', 'odds_draw', 'odds_home', 'match_month']].values
        y_flipped = []
        for val in y:
            if val == 2: y_flipped.append(0)
            elif val == 0: y_flipped.append(2)
            else: y_flipped.append(1)
            
        import numpy as np
        X_combined = np.vstack((X, X_flipped))
        y_combined = np.concatenate((y, y_flipped))
        
        return torch.tensor(X_combined, dtype=torch.float32), torch.tensor(y_combined, dtype=torch.long)

    def train(self, epochs=100):
        X, y = self.load_data()
        if X.shape[0] == 0:
            print("No data found.")
            return

        train_idx = int(len(X) * 0.8)
        X_train, X_val = X[:train_idx], X[train_idx:]
        y_train, y_val = y[:train_idx], y[train_idx:]

        print(f"Training Tower B on {X_train.shape[0]} samples (Augmented)...")
        for epoch in range(epochs):
            self.model.train()
            self.optimizer.zero_grad()
            outputs = self.model(X_train)
            loss = self.criterion(outputs, y_train)
            loss.backward()
            self.optimizer.step()
            self.scheduler.step()
            
            if (epoch+1) % 10 == 0:
                self.model.eval()
                with torch.no_grad():
                    val_outputs = self.model(X_val)
                    _, predicted = torch.max(val_outputs.data, 1)
                    acc = (predicted == y_val).sum().item() / y_val.size(0)
                    print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}, Val Acc: {acc:.2%}')
        
        print("Tower B Training Complete.")
        self.save_model()

    def save_model(self, path="src/models/tower_b.pth"):
        torch.save(self.model.state_dict(), path)
        print(f"Tower B saved to {path}")

    def load_model(self, path="src/models/tower_b.pth"):
        self.model.load_state_dict(torch.load(path))
        self.model.eval()
        print(f"Tower B loaded from {path}")

if __name__ == "__main__":
    trainer = ContextualTowerTrainer()
    trainer.train()
