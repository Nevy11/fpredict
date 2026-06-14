import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key (ensure GEMINI_API_KEY is in your .env)
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class KnowledgeExtractor:
    """
    Advanced NLP Tower: Extracts granular player/team tactical knowledge using Gemini.
    """
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def extract_knowledge(self, text: str):
        """
        Extracts structured facts: {entity, factor_type, impact_score, description}.
        """
        prompt = (
            f"Analyze this EPL news: '{text}'. "
            f"Extract technical insights. Return a JSON object with: "
            f"1. entity (Player/Team name), "
            f"2. factor_type (Training Intensity, Psychology, Skill Improvement, Injury), "
            f"3. impact_score (-0.1 to 0.1), "
            f"4. affected_metric (Goals, Defense, Set-pieces). "
            f"Return ONLY valid JSON."
        )
        
        response = self.model.generate_content(prompt)
        try:
            # Basic cleanup of markdown JSON blocks if present
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        except:
            return None
