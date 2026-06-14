import os
import time
import json
import psycopg2
from dotenv import load_dotenv
from src.models.engine_v2 import FPredictEngineV2

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

class LiveQuantumProcessor:
    """
    Listens for prediction requests and triggers the Quantum Engine.
    """
    def __init__(self):
        self.engine = FPredictEngineV2()
        self.conn = psycopg2.connect(LOCAL_DB_URL)

    def poll_requests(self):
        print("Quantum Live Processor Online. Waiting for requests...")
        while True:
            try:
                with self.conn.cursor() as cur:
                    # 1. Look for pending requests
                    cur.execute("SELECT id, home_team_id, away_team_id FROM prediction_requests WHERE status = 'PENDING' LIMIT 1")
                    request = cur.fetchone()
                    
                    if request:
                        req_id, h_id, a_id = request
                        print(f"New request received: {req_id}. Processing...")
                        
                        # 2. Update status to PROCESSING
                        cur.execute("UPDATE prediction_requests SET status = 'PROCESSING' WHERE id = %s", (req_id,))
                        self.conn.commit()
                        
                        # 3. Handle specific match record (Create one if it doesn't exist for the pair)
                        # For simplicity, we create a temporary match record
                        cur.execute(
                            "INSERT INTO match_records (match_date, home_team_id, away_team_id, competition) VALUES (CURRENT_DATE, %s, %s, 'LIVE_REQUEST') RETURNING id",
                            (h_id, a_id)
                        )
                        match_id = cur.fetchone()[0]
                        
                        # 4. Run Quantum Prediction
                        self.engine.run_comprehensive_prediction(match_id)
                        
                        # 5. Complete request
                        cur.execute("UPDATE prediction_requests SET status = 'COMPLETED' WHERE id = %s", (req_id,))
                        self.conn.commit()
                        print(f"Request {req_id} completed.")
                        
                time.sleep(2) # Poll every 2 seconds
            except Exception as e:
                print(f"Error in processor: {e}")
                time.sleep(5)

if __name__ == "__main__":
    processor = LiveQuantumProcessor()
    processor.poll_requests()
