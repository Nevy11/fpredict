import json
import re

class UnderstatParser:
    """
    Parses Understat pages by extracting JSON from script tags.
    """
    @staticmethod
    def parse_team_data(html_content: str):
        """
        Locates JSON data in script tags and decodes hex-escaped strings.
        """
        # Find all JSON.parse strings
        pattern = re.compile(r"JSON\.parse\(['\"](.+?)['\"]\)")
        matches = pattern.findall(html_content)
        
        combined_data = {}
        for encoded_str in matches:
            try:
                # Decode hex-encoded characters like \x7B
                decoded_str = bytes(encoded_str, "utf-8").decode("unicode_escape")
                # Sometimes it's still hex-encoded after one pass, or has extra escapes
                decoded_str = decoded_str.encode('latin1').decode('unicode_escape')
                
                data = json.loads(decoded_str)
                if isinstance(data, dict):
                    combined_data.update(data)
                elif isinstance(data, list):
                    # If it's a list, we might need a specific key
                    combined_data['list_data'] = data
            except Exception as e:
                continue
                
        return combined_data if combined_data else None
