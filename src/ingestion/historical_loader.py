import pandas as pd
import psycopg2
import os
import glob
from dotenv import load_dotenv
from supabase import create_client

# Load credentials
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SERVICE_ROLE_KEY")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class HistoricalLoader:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.local_conn = psycopg2.connect(LOCAL_DB_URL)
        self.team_cache_local = {}
        self.team_cache_supabase = {}

    def get_local_team_id(self, team_name):
        if team_name in self.team_cache_local:
            return self.team_cache_local[team_name]
        
        with self.local_conn.cursor() as cur:
            cur.execute("SELECT id FROM teams WHERE team_name = %s", (team_name,))
            res = cur.fetchone()
            if res:
                self.team_cache_local[team_name] = res[0]
                return res[0]
            
            cur.execute("INSERT INTO teams (team_name) VALUES (%s) RETURNING id", (team_name,))
            new_id = cur.fetchone()[0]
            self.local_conn.commit()
            self.team_cache_local[team_name] = new_id
            return new_id

    def get_supabase_team_id(self, team_name):
        if team_name in self.team_cache_supabase:
            return self.team_cache_supabase[team_name]
            
        # Check Supabase
        res = self.supabase.table("teams").select("id").eq("team_name", team_name).execute()
        if res.data:
            tid = res.data[0]['id']
            self.team_cache_supabase[team_name] = tid
            return tid
            
        # Insert to Supabase
        ins_res = self.supabase.table("teams").insert({"team_name": team_name}).execute()
        if ins_res.data:
            tid = ins_res.data[0]['id']
            self.team_cache_supabase[team_name] = tid
            return tid
        return None

    def load_file(self, file_path):
        # Read with flexible date parsing
        df = pd.read_csv(file_path)
        print(f"Loading {len(df)} rows from {file_path}...")
        
        for _, row in df.iterrows():
            try:
                # Handle potential NaN or empty team names
                if pd.isna(row.get('HomeTeam')) or pd.isna(row.get('AwayTeam')):
                    continue
                    
                # 1. Get IDs for BOTH databases
                local_h_id = self.get_local_team_id(str(row['HomeTeam']))
                local_a_id = self.get_local_team_id(str(row['AwayTeam']))
                
                sb_h_id = self.get_supabase_team_id(str(row['HomeTeam']))
                sb_a_id = self.get_supabase_team_id(str(row['AwayTeam']))
                
                match_date = pd.to_datetime(row['Date'], dayfirst=True).strftime('%Y-%m-%d')
                fthg = int(row['FTHG'])
                ftag = int(row['FTAG'])
                
                # Extract Odds
                odds_h = float(row.get('B365H', 0)) if not pd.isna(row.get('B365H')) else 0.0
                odds_d = float(row.get('B365D', 0)) if not pd.isna(row.get('B365D')) else 0.0
                odds_a = float(row.get('B365A', 0)) if not pd.isna(row.get('B365A')) else 0.0
                
                # 2. Insert Local
                with self.local_conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO match_records 
                           (match_date, competition, home_team_id, away_team_id, home_goals, away_goals, odds_home, odds_draw, odds_away) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (match_date, 'EPL', local_h_id, local_a_id, fthg, ftag, odds_h, odds_d, odds_a)
                    )
                self.local_conn.commit()
                
                # 3. Insert Supabase
                if sb_h_id and sb_a_id:
                    try:
                        self.supabase.table("match_records").insert({
                            "match_date": match_date,
                            "competition": "EPL",
                            "home_team_id": sb_h_id,
                            "away_team_id": sb_a_id,
                            "home_goals": fthg,
                            "away_goals": ftag,
                            "odds_home": odds_h,
                            "odds_draw": odds_d,
                            "odds_away": odds_a
                        }).execute()
                    except Exception as e:
                        print(f"Warning: Supabase match insert failed: {e}")
            except Exception as e:
                print(f"Error loading row: {e}")
                self.local_conn.rollback() # Crucial: Reset the transaction state on failure
                continue
                
        print(f"Finished loading {file_path}")

if __name__ == "__main__":
    loader = HistoricalLoader()
    files = glob.glob("data/historical_csvs/EPL_*.csv")
    for file in files:
        loader.load_file(file)
