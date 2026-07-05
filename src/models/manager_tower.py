import os

import pandas as pd
import psycopg2
import xgboost as xgb
from dotenv import load_dotenv
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from src.managers.repository import ManagerRepository

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

FEATURE_COLUMNS = [
    "h_mgr_ppg",
    "a_mgr_ppg",
    "mgr_ppg_diff",
    "h_mgr_win_rate",
    "a_mgr_win_rate",
    "mgr_win_rate_diff",
    "h_mgr_style",
    "a_mgr_style",
    "mgr_style_diff",
    "mgr_h2h_meetings",
    "mgr_h2h_home_wins",
    "mgr_h2h_away_wins",
]


class ManagerTower:
    def __init__(self):
        self.conn = psycopg2.connect(LOCAL_DB_URL)
        self.repo = ManagerRepository()
        self.model = xgb.XGBClassifier(
            n_estimators=120,
            learning_rate=0.08,
            max_depth=4,
            objective="multi:softprob",
            random_state=42,
        )
        self.model_path = "src/models/manager_tower.json"

    def load_training_data(self):
        query = """
            SELECT m.match_date, th.team_name AS home_team, ta.team_name AS away_team,
                   m.home_goals, m.away_goals
            FROM match_records m
            JOIN teams th ON m.home_team_id = th.id
            JOIN teams ta ON m.away_team_id = ta.id
            WHERE m.home_goals IS NOT NULL
              AND m.away_goals IS NOT NULL
              AND m.match_date >= '2010-08-01'
            ORDER BY m.match_date ASC
        """
        matches = pd.read_sql(query, self.conn)
        rows = []

        for _, match in matches.iterrows():
            features = self.repo.build_feature_vector(
                match["home_team"],
                match["away_team"],
                match_date=match["match_date"],
            )
            target = 1
            if match["home_goals"] > match["away_goals"]:
                target = 2
            elif match["home_goals"] < match["away_goals"]:
                target = 0
            rows.append({**features, "target": target})

        return pd.DataFrame(rows)

    def train(self):
        dataset = self.load_training_data()
        if dataset.empty:
            raise RuntimeError("No manager training data available.")

        x = dataset[FEATURE_COLUMNS]
        y = dataset["target"]
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
        self.model.fit(x_train, y_train)
        accuracy = accuracy_score(y_test, self.model.predict(x_test))
        print(f"Manager Tower trained on {len(dataset)} fixtures. Validation accuracy: {accuracy:.2%}")
        self.save_model()
        return accuracy

    def predict_proba(self, feature_vector: dict[str, float]):
        frame = pd.DataFrame([{column: feature_vector[column] for column in FEATURE_COLUMNS}])
        return self.model.predict_proba(frame)[0]

    def save_model(self, path: str | None = None):
        target = path or self.model_path
        self.model.save_model(target)
        print(f"Manager Tower saved to {target}")

    def load_model(self, path: str | None = None):
        target = path or self.model_path
        self.model.load_model(target)
        print(f"Manager Tower loaded from {target}")

    def close(self):
        self.repo.close()
        self.conn.close()


if __name__ == "__main__":
    tower = ManagerTower()
    tower.train()
    tower.close()
