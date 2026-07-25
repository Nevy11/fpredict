const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000/fixtures', { waitUntil: 'networkidle' });
  await page.screenshot({ path: 'fixtures_page_debug.png' });
  await browser.close();
})();
