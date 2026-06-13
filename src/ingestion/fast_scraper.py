from .base_scrapers import BaseScraper
import asyncio

class FastScraper(BaseScraper):
    """
    Tier 1 Scraper using curl_cffi.
    Mimics TLS/HTTP2 fingerprints to bypass WAFs (Cloudflare/Akamai).
    """
    def __init__(self):
        super().__init__()

    async def get_raw_data(self, url: str):
        print(f"Fetching {url} using curl_cffi...")
        data = await self.fetch(url)
        if data:
            print(f"Successfully fetched {len(data)} characters.")
        return data

# Example usage for testing
if __name__ == "__main__":
    scraper = FastScraper()
    url = "https://www.wikipedia.org"  # Updated to a more neutral famous site
    asyncio.run(scraper.get_raw_data(url))
