import json
import re

class UnderstatParser:
    """
    Parses Understat pages by extracting JSON from script tags.
    """
    @staticmethod
    def parse_team_data(html_content: str):
        """
        Locates 'teamsData' or 'groupsData' in script tags and parses JSON.
        """
        # Regex to find the JSON data inside the script tag
        pattern = re.compile(r"JSON\.parse\('([^']+)'\)")
        match = pattern.search(html_content)
        
        if match:
            # Understat escapes data inside the string, need to unescape
            json_str = match.group(1).encode('utf-8').decode('unicode_escape')
            return json.loads(json_str)
        else:
            print("Could not locate JSON data in Understat page.")
            return None
