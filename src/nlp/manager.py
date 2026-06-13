import os
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

    def process_unprocessed_news(self):
        # 1. Fetch unprocessed records
        response = self.supabase.table("unstructured_news")\
            .select("*").eq("processed", False).execute()
        
        news_items = response.data
        print(f"Found {len(news_items)} news items to process.")

        # 2. Analyze and update
        for item in news_items:
            score = self.analyzer.analyze(item['raw_text'])
            print(f"Processed item {item['id']}: Sentiment={score}")
            
            self.supabase.table("unstructured_news").update({
                "sentiment_score": score,
                "processed": True
            }).eq("id", item['id']).execute()

if __name__ == "__main__":
    manager = NLPManager()
    manager.process_unprocessed_news()
