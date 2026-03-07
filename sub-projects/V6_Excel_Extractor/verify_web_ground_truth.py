import asyncio, json, math, os, sys
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except:
    pass

sys.path.insert(0, str(ROOT / 'sub-projects' / 'V2_Data_Pipeline'))

try:
    from pipeline import get_supabase
except ImportError:
    pass


# Stealth
try:
    from playwright_stealth import stealth_async
except:
    stealth_async = None

async def extract_web_table_for_ticker(ticker: str):
    print(f"[{ticker}] Scrape Web DOM table ...")
    
    table_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a real user agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        if stealth_async:
            await stealth_async(page)
            
        url = f"https://trading.vietcap.com.vn/iq/company?ticker={ticker}&tab=financial&isIndex=false&financialTab=financialStatement"
        print(f"[{ticker}] navigating to {url}")
        
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)
        
        # Click "Năm"
        try:
            nam_btn = page.locator("button:has-text('Năm')").first
            await nam_btn.click(timeout=10000)
            await asyncio.sleep(3)
        except Exception as e:
            print(f"[{ticker}] Không tìm thấy nút 'Năm', dùng mặc định (Quý). {e}")

        # The grid is an AG-Grid or custom rendered component.
        # We find all typical row containers
        rows = await page.evaluate('''() => {
            const results = [];
            // Try different possible row selectors
            const rowEls = document.querySelectorAll('.ag-row, [role="row"], tr');
            rowEls.forEach(row => {
                const cells = row.querySelectorAll('.ag-cell, [role="gridcell"], [role="columnheader"], td, th');
                if (cells && cells.length > 0) {
                    const rowTexts = [];
                    cells.forEach(c => rowTexts.push(c.innerText.trim()));
                    results.push(rowTexts);
                }
            });
            return results;
        }''')
        
        await browser.close()
        
    return rows

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="MBB")
    args = parser.parse_args()
    
    rows = asyncio.run(extract_web_table_for_ticker(args.ticker))
    print(f"Found {len(rows)} DOM rows.")
    for i, r in enumerate(rows[:5]):
        print(f"Row {i}:", r)
