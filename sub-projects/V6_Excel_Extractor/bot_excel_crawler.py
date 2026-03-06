import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path

# Adjust CWD to root if needed
ROOT = Path(__file__).parent.parent.parent
DOWNLOAD_DIR = ROOT / "data" / "excel_imports"

async def download_excel(ticker: str):
    print(f"[{ticker}] Khởi động trình duyệt tải Excel...")
    
    # Tạo thư mục tải nếu chưa có
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Thiết lập mô phỏng người dùng thực
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True
        )
        
        # Áp dụng Stealth plugin
        try:
            from playwright_stealth import stealth_async
        except ImportError:
            stealth_async = None
            
        page = await context.new_page()
        if stealth_async:
            await stealth_async(page)
            
        target_url = f"https://trading.vietcap.com.vn/iq/company?ticker={ticker}&tab=financial&isIndex=false&financialTab=financialStatement"
        print(f"[{ticker}] Đang truy cập: {target_url} ...")
        
        # Chờ page load hoàn thành (khuyến nghị networkidle với web React/Vue)
        await page.goto(target_url, wait_until="networkidle")
        
        print(f"[{ticker}] Đang tìm nút 'Tải xuống'...")
        # Tìm nút có text "Tải xuống"
        # Wait specifically for the button to appear in DOM
        try:
            download_btn = page.locator("button:has-text('Tải xuống')").first
            await download_btn.wait_for(state="visible", timeout=15000)
            
            print(f"[{ticker}] Đã tìm thấy nút Tải xuống. Bắt đầu bắt sự kiện Download...")
            
            # Click and wait for download
            async with page.expect_download(timeout=30000) as download_info:
                await download_btn.click()
                
            download = await download_info.value
            
            # Lưu file
            file_name = f"{ticker}_BCTC_Vietcap.xlsx"
            file_path = DOWNLOAD_DIR / file_name
            await download.save_as(str(file_path))
            
            print(f"✅ [{ticker}] Tải thành công! File lưu tại: {file_path}")
            
        except Exception as e:
            print(f"❌ [{ticker}] Lỗi khi tải file: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(download_excel("MBB"))
