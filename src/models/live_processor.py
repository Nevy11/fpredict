import os
import time
import asyncio
import json
import psycopg2
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timezone
from src.models.engine_v2 import FPredictEngineV2
from src.ingestion.pipeline import IngestionPipeline

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SERVICE_ROLE_KEY")
LOCAL_DB_URL = f"dbname=fpredict_db user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} host=localhost"

class LiveQuantumProcessor:
    def __init__(self):
        self.engine = FPredictEngineV2()
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.conn = psycopg2.connect(LOCAL_DB_URL)
        self.pipeline = IngestionPipeline()
        self.start_time = datetime.now(timezone.utc).isoformat()

    async def run(self):
        print(f"Quantum Live Processor Online. Ignoring requests before {self.start_time}")
        while True:
            try:
                # 1. Look for NEW pending requests on REMOTE Supabase
                response = self.supabase.table("prediction_requests")\
                    .select("*").eq("status", "PENDING").gt("created_at", self.start_time).limit(1).execute()
                
                if response.data:
                    req = response.data[0]
                    req_id, h_id, a_id = req['id'], req['home_team_id'], req['away_team_id']
                    
                    # Fetch names for scraping
                    with self.conn.cursor() as cur:
                        cur.execute("SELECT team_name FROM teams WHERE id = %s", (h_id,))
                        h_name = cur.fetchone()[0]
                        cur.execute("SELECT team_name FROM teams WHERE id = %s", (a_id,))
                        a_name = cur.fetchone()[0]

                    print(f"\n[EVENT] New request: {h_name} vs {a_name}")
                    
                    # 2. Stage: Real-time News Scraping & Refinement
                    print(f"[INGEST] Fetching fresh news for {h_name} & {a_name}...")
                    await self.pipeline.fetch_latest_news(h_name)
                    await self.pipeline.fetch_latest_news(a_name)
                    
                    # 3. Create match record
                    with self.conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO match_records (match_date, home_team_id, away_team_id, competition) VALUES (CURRENT_DATE, %s, %s, 'LIVE_REQUEST') RETURNING id",
                            (h_id, a_id)
                        )
                        match_id = cur.fetchone()[0]
                        self.conn.commit()

                        # Sync this match record to Supabase
                        cur.execute("SELECT * FROM match_records WHERE id = %s", (match_id,))
                        m_row = cur.fetchone()
                        m_cols = [desc[0] for desc in cur.description]
                        m_dict = dict(zip(m_cols, m_row))
                        for k, v in m_dict.items():
                            if not isinstance(v, (int, float, str, bool, dict, list)) and v is not None:
                                m_dict[k] = str(v)
                        self.supabase.table("match_records").upsert(m_dict).execute()
                        
                        # Added propagation delay
                        await asyncio.sleep(1)

                        # 4. Run Quantum Prediction
                        print(f"[ENGINE] Running Quantum Engine...")
                        prediction = self.engine.run_comprehensive_prediction(match_id)
                        
                        # 5. Sync results
                        cur.execute("UPDATE unstructured_news SET processed = TRUE WHERE processed = FALSE")
                        self.conn.commit()

                        cur.execute("SELECT * FROM predictions WHERE match_id = %s", (match_id,))
                        p_row = cur.fetchone()
                        if p_row:
                            p_cols = [desc[0] for desc in cur.description]
                            p_dict = dict(zip(p_cols, p_row))
                            for k, v in p_dict.items():
                                if not isinstance(v, (int, float, str, bool, dict, list)) and v is not None:
                                    p_dict[k] = str(v)
                            p_dict['version_id'] = f"live-{req_id}" 

                            # Safely attempt to sync to remote
                            try:
                                self.supabase.table("predictions").upsert(p_dict).execute()
                            except Exception as e:
                                print(f"[WARNING] Remote sync partial failure (likely schema mismatch): {e}")

                    # 6. Complete request
                    self.supabase.table("prediction_requests").update({"status": "COMPLETED"}).eq("id", req_id).execute()
                    print(f"[SUCCESS] Request {req_id} completed.")
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    processor = LiveQuantumProcessor()
    asyncio.run(processor.run())
