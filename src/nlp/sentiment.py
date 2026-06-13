import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key (ensure GEMINI_API_KEY is in your .env)
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class SentimentAnalyzer:
    """
    Analyzes raw text for football-related sentiment using Gemini.
    """
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def analyze(self, text: str):
        """
        Rates sentiment on a scale of -0.05 (negative) to +0.05 (positive).
        """
        prompt = (
            f"Analyze the following EPL news text and return ONLY a single float "
            f"value between -0.05 and +0.05 based on the expected impact on "
            f"team performance: '{text}'"
        )
        
        response = self.model.generate_content(prompt)
        try:
            return float(response.text.strip())
        except ValueError:
            return 0.0 # Neutral fallback
