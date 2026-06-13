import asyncio
from curl_cffi.requests import AsyncSession

class BaseScraper:
    def __init__(self):
        self.session = AsyncSession(impersonate="chrome110")
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://fbref.com/",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="110", "Google Chrome";v="110"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Upgrade-Insecure-Requests": "1"
        }

    async def fetch(self, url: str):
        """Generic fetch method to be overridden or used as is."""
        try:
            response = await self.session.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
