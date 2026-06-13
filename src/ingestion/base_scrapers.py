import asyncio
from curl_cffi.requests import AsyncSession

class BaseScraper:
    def __init__(self):
        self.session = AsyncSession(impersonate="chrome110")

    async def fetch(self, url: str):
        """Generic fetch method to be overridden or used as is."""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
