import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_HOST = "db.agojvvfjajkkpqohehcm.supabase.co"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "Skyworth.95"
DB_PORT = "5432"

def create_managers_table():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        sql = """
        CREATE TABLE IF NOT EXISTS current_managers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            team_name VARCHAR(255) UNIQUE NOT NULL,
            manager_name VARCHAR(255) NOT NULL,
            tactical_style VARCHAR(50),
            last_5_games JSONB,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
        );
        NOTIFY pgrst, 'reload schema';
        """
        
        cur.execute(sql)
        conn.commit()
        print("Remote Supabase table 'current_managers' created successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error updating remote schema: {e}")

if __name__ == "__main__":
    create_managers_table()
