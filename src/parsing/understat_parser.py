import json
import re
import pandas as pd

class UnderstatParser:
    """
    Parses Understat pages by extracting JSON from script tags.
    """
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
