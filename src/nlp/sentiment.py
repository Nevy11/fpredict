import os
import json
import torch
from transformers import pipeline
from dotenv import load_dotenv

load_dotenv()

class KnowledgeExtractor:
    """
    Pure Python NLP Tower: Extracts tactical knowledge using a local TinyLlama model.
    100% Free, Unlimited, and self-contained (no Ollama/API needed).
    """
    def __init__(self, model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        print(f"Loading local AI model ({model_id})...")
        self.pipe = pipeline(
            "text-generation", 
            model=model_id, 
            torch_dtype=torch.float32, # Use float16 if you have a GPU
            device_map="auto"
        )

    def extract_knowledge(self, text: str):
        """
        Extracts structured facts using the local LLM.
        """
        print(f"[AI] Analyzing news snippet: {text[:50]}...")
        
        messages = [
            {"role": "system", "content": "You are a specialized soccer analytics assistant. Output ONLY a valid raw JSON object."},
            {"role": "user", "content": f"Analyze this EPL news: '{text}'. Return JSON with: entity, impact_score (-0.1 to 0.1), affected_metric."}
        ]
        
        prompt = self.pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        try:
            print("[AI] Running model inference...")
            outputs = self.pipe(
                prompt, 
                max_new_tokens=128, # Reduced for speed
                do_sample=False,    # Greedy decoding is faster and more stable
                temperature=None, 
                top_p=None
            )
            print("[AI] Inference complete. Extracting JSON...")
            content = outputs[0]["generated_text"].split("<|assistant|>")[-1].strip()
            
            # Robust JSON extraction
            import re
            json_match = re.search(r"(\{.*\})", content, re.DOTALL)
            if json_match:
                clean_json = json_match.group(1)
                data = json.loads(clean_json)
                print(f"[AI] Success: Found {data.get('entity')}")
                return data
            
            print(f"[AI] Warning: No JSON found in output.")
            return None
        except Exception as e:
            print(f"[AI] Error: {e}")
            return None
