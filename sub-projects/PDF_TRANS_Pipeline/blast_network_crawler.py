import requests
import time
import random
import json
import os
from typing import List, Dict

# Thiết lập đường dẫn lưu trữ tạm
TMP_DIR = os.path.join(os.path.dirname(__file__), '.tmp')
os.makedirs(TMP_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(TMP_DIR, 'link_list.json')

# Cấu hình API endpoints (Ví dụ: Fireant API cho Báo cáo tài chính)
# Thay URL thực tế sau khi bắt được đúng network gói tin từ màn hình BCTC.
API_URL = "https://restv2.fireant.vn/symbols/{symbol}/financial-reports" 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://fireant.vn/",
    # Bổ sung Authorization Token nếu cần thiết
}

def fetch_financial_reports(symbol: str, retries: int = 3, backoff_factor: float = 2.0) -> List[Dict]:
    """
    Kéo danh sách báo cáo tài chính qua Network XHR/API, áp dụng Retry & Exponential Backoff.
    """
    url = API_URL.format(symbol=symbol)
    
    for attempt in range(retries):
        try:
            print(f"[{symbol}] Fetching data... Attempt {attempt + 1}/{retries}")
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[{symbol}] Success! Retrieved API data.")
                return data
            elif response.status_code == 429:
                print(f"[{symbol}] Rate limited (429). Retrying...")
            else:
                print(f"[{symbol}] Failed with status code {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"[{symbol}] Error: {e}")
            
        # Exponential backoff + Jitter
        sleep_time = (backoff_factor ** attempt) + random.uniform(0, 1)
        print(f"[{symbol}] Waiting {sleep_time:.2f}s before next attempt...")
        time.sleep(sleep_time)
        
    print(f"[{symbol}] Exhausted all {retries} retry attempts.")
    return []

def extract_pdf_links(api_data: List[Dict]) -> List[Dict]:
    """
    Lọc và trích xuất link PDF từ cục response JSON trả về.
    """
    pdf_links = []
    # Logic phụ thuộc vào cấu trúc thực tế của JSON
    # Giả sử cấu trúc có trường 'documentUrl' và 'title'
    for item in api_data:
        title = item.get("title", "")
        url = item.get("documentUrl", "")
        if url and url.endswith(".pdf"):
            if any(keyword in title.lower() for keyword in ["báo cáo tài chính", "bctc", "báo cáo tài chính hợp nhất"]):
                pdf_links.append({
                    "title": title,
                    "url": url,
                    "period": item.get("period", ""),
                    "year": item.get("year", "")
                })
    return pdf_links

def run_crawler(symbols: List[str]):
    all_links = {}
    for sym in symbols:
        raw_data = fetch_financial_reports(sym)
        if raw_data:
            links = extract_pdf_links(raw_data)
            all_links[sym] = links
            
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_links, f, ensure_ascii=False, indent=4)
    print(f"Crawl completed. PDF links saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    test_symbols = ['VNM', 'FPT', 'HPG']
    run_crawler(test_symbols)
