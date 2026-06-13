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
    Ingests text sentiment and SDI to model structural disruptions.
    Deeper architecture with Batch Normalization and Dropout for better generalization.
    """
    def __init__(self, input_size=4, hidden_dims=[32, 64, 32]):
        super(TowerB, self).__init__()
        
        layers = []
        current_dim = input_size
        
        for h_dim in hidden_dims:
            layers.append(nn.Linear(current_dim, h_dim))
            layers.append(nn.BatchNorm1d(h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            current_dim = h_dim
            
        self.feature_extractor = nn.Sequential(*layers)
        self.output_layer = nn.Linear(current_dim, 3) # Away, Draw, Home

    def forward(self, x):
        features = self.feature_extractor(x)
        logits = self.output_layer(features)
        return logits

class ContextualTowerTrainer:
    def __init__(self):
        self.conn = psycopg2.connect(LOCAL_DB_URL)
        self.model = TowerB()
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)

    def load_data(self):
        print("Loading contextual data for Tower B...")
        query = """
            SELECT 
                (h.features->>'sdi')::float as h_sdi,
                (h.features->>'sentiment_score')::float as h_sentiment,
                (a.features->>'sdi')::float as a_sdi,
                (a.features->>'sentiment_score')::float as a_sentiment,
                m.home_goals,
                m.away_goals
            FROM match_records m
            JOIN feature_store h ON m.home_team_id = h.team_id
            JOIN feature_store a ON m.away_team_id = a.team_id
        """
        df = pd.read_sql(query, self.conn)
        
        X = torch.tensor(df[['h_sdi', 'h_sentiment', 'a_sdi', 'a_sentiment']].values, dtype=torch.float32)
        
        y = []
        for _, row in df.iterrows():
            if row['home_goals'] > row['away_goals']: y.append(2)
            elif row['home_goals'] == row['away_goals']: y.append(1)
            else: y.append(0)
        y = torch.tensor(y, dtype=torch.long)
        
        return X, y

    def train(self, epochs=50):
        X, y = self.load_data()
        if X.shape[0] == 0:
            print("No data found for training.")
            return

        print(f"Training Tower B on {X.shape[0]} samples...")
        for epoch in range(epochs):
            self.optimizer.zero_grad()
            outputs = self.model(X)
            loss = self.criterion(outputs, y)
            loss.backward()
            self.optimizer.step()
            
            if (epoch+1) % 10 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')
        
        print("Tower B Training Complete.")

if __name__ == "__main__":
    trainer = ContextualTowerTrainer()
    trainer.train()
