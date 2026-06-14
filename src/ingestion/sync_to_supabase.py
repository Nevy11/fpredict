import os
import psycopg2
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SERVICE_ROLE_KEY")

class SupabaseSyncer:
    def __init__(self):
        self.local_conn = psycopg2.connect(LOCAL_DB_URL)
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    def sync_table(self, table_name):
        print(f"Syncing table: {table_name}...")
        with self.local_conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {table_name}")
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            
            data_to_upsert = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                # Convert UUIDs/Dates to strings for JSON serialization
                for k, v in row_dict.items():
                    if not isinstance(v, (int, float, str, bool, dict, list)) and v is not None:
                        row_dict[k] = str(v)
                data_to_upsert.append(row_dict)
            
            if data_to_upsert:
                # Upsert in batches of 100
                for i in range(0, len(data_to_upsert), 100):
                    batch = data_to_upsert[i:i+100]
                    # Use on_conflict for teams table to handle existing team names
                    if table_name == "teams":
                        self.supabase.table(table_name).upsert(batch, on_conflict="team_name").execute()
                    else:
                        self.supabase.table(table_name).upsert(batch).execute()
                print(f"Successfully synced {len(data_to_upsert)} rows to Supabase.")

if __name__ == "__main__":
    syncer = SupabaseSyncer()
    tables = [
        "teams", 
        "players", 
        "squad_membership", 
        "match_records", 
        "unstructured_news", 
        "feature_store", 
        "player_impact_metrics", 
        "player_performance",
        "player_metadata",
        "predictions",
        "prediction_requests"
    ]
    for table in tables:
        syncer.sync_table(table)
