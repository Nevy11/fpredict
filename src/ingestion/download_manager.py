import os
import requests
import pandas as pd

class DownloadManager:
    def __init__(self, base_url="https://www.football-data.co.uk/mmz4281"):
        self.base_url = base_url
        self.download_dir = "data/historical_csvs"
        os.makedirs(self.download_dir, exist_ok=True)

    def download_epl_season(self, season_short):
        """
        season_short format: '2021', '2122' etc. 
        Note: Football-data.co.uk uses specific season formats in URLs.
        E.g., 2024/25 season is '2425/E0.csv'
        """
        url = f"{self.base_url}/{season_short}/E0.csv"
        file_path = os.path.join(self.download_dir, f"EPL_{season_short}.csv")
        
        print(f"Downloading {url}...")
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Saved to {file_path}")
            return file_path
        else:
            print(f"Failed to download {url}. Status code: {response.status_code}")
            return None

if __name__ == "__main__":
    manager = DownloadManager()
    # Targeting 15 seasons to reach 5,000+ matches
    seasons = [
        "2425", "2324", "2223", "2122", "2021", 
        "1920", "1819", "1718", "1617", "1516", 
        "1415", "1314", "1213", "1112", "1011"
    ]
    for season in seasons:
        manager.download_epl_season(season)
