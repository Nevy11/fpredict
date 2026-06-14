import json
import re
import pandas as pd

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
                
                data = json.loads(decoded_str)
                if isinstance(data, dict):
                    combined_data.update(data)
                elif isinstance(data, list):
                    # Try to identify what this list is
                    if len(data) > 0 and 'id' in data[0] and ('xG' in data[0] or 'isResult' in data[0]):
                        if 'isResult' in data[0]:
                            combined_data['datesData'] = data
                        else:
                            combined_data['playersData'] = data
                    else:
                        combined_data['list_data'] = data
            except Exception as e:
                continue
                
        return combined_data if combined_data else None

    @staticmethod
    def parse_player_table(html_content: str):
        """
        Parses the player statistics table from an Understat team page.
        """
        import io
        try:
            # Understat player tables are usually the only ones with many rows
            dfs = pd.read_html(io.StringIO(html_content))
            # The player table is typically the first or second one
            for df in dfs:
                if 'Player' in df.columns or 'player_name' in df.columns or 'Pos' in df.columns:
                    return df
            return dfs[0] if dfs else None
        except Exception as e:
            print(f"Error parsing Understat table: {e}")
            return None
