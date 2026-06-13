from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from .base_scrapers import BaseScraper
import asyncio

class BrowserScraper(BaseScraper):
    """
    Tier 2 Scraper using Playwright + Stealth.
    Handles JavaScript rendering and bypasses browser-based WAFs.
    """
    def __init__(self):
        super().__init__()

    async def get_raw_data(self, url: str):
        print(f"Fetching {url} using Playwright+Stealth...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Apply stealth
            stealth_config = Stealth()
            await stealth_config.apply_stealth_async(page)
            
            try:
                await page.goto(url, wait_until="networkidle")
                content = await page.content()
                print(f"Successfully fetched {len(content)} characters via browser.")
                return content
            except Exception as e:
                print(f"Error fetching {url} with browser: {e}")
                return None
            finally:
                await browser.close()

# Example usage for testing
if __name__ == "__main__":
    scraper = BrowserScraper()
    # Using a site that requires JS to render content
    url = "https://www.wikipedia.org" 
    asyncio.run(scraper.get_raw_data(url))
