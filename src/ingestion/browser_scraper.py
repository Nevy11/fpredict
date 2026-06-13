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
        print(f"Fetching {url} using Playwright+Stealth (Persistent Context)...")
        user_data_dir = "/tmp/playwright_user_data"
        async with async_playwright() as p:
            # Persistent context saves cookies/session state which helps bypass challenges
            context = await p.chromium.launch_persistent_context(
                user_data_dir,
                headless=True,
                slow_mo=50,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            # Apply stealth
            stealth_config = Stealth()
            await stealth_config.apply_stealth_async(page)
            
            try:
                # 1. Initial visit
                await page.goto(url, wait_until="domcontentloaded", timeout=90000)
                
                # 2. Add human-like jitter
                await asyncio.sleep(5) 
                await page.mouse.move(500, 500)
                await page.evaluate("window.scrollTo(0, 500)")
                
                # 3. Wait for the specific FBref or Understat selectors
                if "fbref.com" in url:
                    await page.wait_for_selector("table", timeout=30000)
                
                content = await page.content()
                print(f"Successfully fetched {len(content)} characters.")
                return content
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return None
            finally:
                await context.close()

# Example usage for testing
if __name__ == "__main__":
    scraper = BrowserScraper()
    # Using a site that requires JS to render content
    url = "https://www.wikipedia.org" 
    asyncio.run(scraper.get_raw_data(url))
