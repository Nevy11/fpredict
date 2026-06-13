import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class EloCalculator:
    """
    Calculates dynamic Elo ratings for teams based on match history.
    """
    def __init__(self, k_factor=20):
        self.k_factor = k_factor
        self.ratings = {} # team_name -> rating
        self.conn = psycopg2.connect(LOCAL_DB_URL)

    def get_expected_score(self, rating_a, rating_b):
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def update_ratings(self, home_team, away_team, home_goals, away_goals):
        r_h = self.ratings.get(home_team, 1500)
        r_a = self.ratings.get(away_team, 1500)
        
        e_h = self.get_expected_score(r_h, r_a)
        e_a = 1 - e_h
        
        # Result: 1 (Home Win), 0.5 (Draw), 0 (Away Win)
        s_h = 0.5
        if home_goals > away_goals: s_h = 1
        elif home_goals < away_goals: s_h = 0
        s_a = 1 - s_h
        
        new_r_h = r_h + self.k_factor * (s_h - e_h)
        new_r_a = r_a + self.k_factor * (s_a - e_a)
        
        self.ratings[home_team] = new_r_h
        self.ratings[away_team] = new_r_a
        return new_r_h, new_r_a

    def run_historical(self):
        print("Calculating historical Elo ratings...")
        query = """
            SELECT m.match_date, h.team_name as h_name, a.team_name as a_name, m.home_goals, m.away_goals
            FROM match_records m
            JOIN teams h ON m.home_team_id = h.id
            JOIN teams a ON m.away_team_id = a.id
            ORDER BY m.match_date ASC
        """
        df = pd.read_sql(query, self.conn)
        
        for _, row in df.iterrows():
            self.update_ratings(row['h_name'], row['a_name'], row['home_goals'], row['away_goals'])
        
        print(f"Calculated Elo for {len(self.ratings)} teams.")
        return self.ratings

if __name__ == "__main__":
    calc = EloCalculator()
    final_ratings = calc.run_historical()
    for team, elo in sorted(final_ratings.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"{team}: {elo:.2f}")
