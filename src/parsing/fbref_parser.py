import pandas as pd
from bs4 import BeautifulSoup
import io

class FBrefParser:
    """
    Parses FBref HTML pages into structured Pandas DataFrames.
    """
    @staticmethod
    def parse_squad_stats(html_content: str):
        """
        Parses standard squad stats table from FBref.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # FBref tables are often wrapped in div#all_stats_standard
        # Using pandas read_html is the most efficient way to handle these tables
        try:
            dfs = pd.read_html(io.StringIO(str(soup)))
            # Usually the first table is the one we want, 
            # but we might need to be specific based on the page structure.
            return dfs[0]
        except Exception as e:
            print(f"Error parsing FBref table: {e}")
            return None
