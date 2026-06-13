import os
import psycopg2
from dotenv import load_dotenv
from supabase import create_client
from .sentiment import SentimentAnalyzer

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SERVICE_ROLE_KEY")

class NLPManager:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.analyzer = SentimentAnalyzer()
        self.local_conn = psycopg2.connect(f"dbname=fpredict_db user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} host=localhost")

    def process_unprocessed_news_local(self):
        print("Processing news from local DB...")
        with self.local_conn.cursor() as cur:
            cur.execute("SELECT id, raw_text FROM unstructured_news WHERE processed = FALSE")
            news_items = cur.fetchall()
            print(f"Found {len(news_items)} news items to process locally.")

            for item_id, text in news_items:
                score = self.analyzer.analyze(text)
                print(f"Processed item {item_id}: Sentiment={score}")
                
                cur.execute(
                    "UPDATE unstructured_news SET sentiment_score = %s, processed = TRUE WHERE id = %s",
                    (score, item_id)
                )
            self.local_conn.commit()

if __name__ == "__main__":
    manager = NLPManager()
    manager.process_unprocessed_news()
