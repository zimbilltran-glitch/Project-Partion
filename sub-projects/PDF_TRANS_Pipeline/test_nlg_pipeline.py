"""
PDF_TRANS Test Script: NLG Financial Reports (4 Quarters)
Mục đích: Dry-run kiểm tra pipeline Fireant → Long Format output
         Chỉ in ra Terminal, KHÔNG ghi vào DB nào (Cả Staging lẫn Production)
"""
import os
import sys
import json
import requests
import logging
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [TEST-NLG] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── Config ─────────────────────────────────────────────────────────────────
SYMBOL = "NLG"
FIREANT_TYPES = {"CDKT": 1, "KQKD": 2, "LCTT_TT": 3, "LCTT_GT": 4}

# 4 Quý gần nhất: Q1-2024 → Q4-2024
# Fireant returns multiple periods per API call, we'll filter to last 4 quarters
TARGET_PERIODS = ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]

def get_bearer_token_simple():
    """Lấy Bearer Token từ Playwright - Reuse logic từ fetch_fireant.py"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Missing playwright. pip install playwright && playwright install chromium")
        return None

    logger.info("Spawning Playwright to capture Bearer Token for NLG...")
    token = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        def handle_request(request):
            nonlocal token
            if token: return
            headers = request.headers
            if "authorization" in headers and "Bearer" in headers["authorization"]:
                token = headers["authorization"]

        page.on("request", handle_request)
        page.goto(
            f"https://fireant.vn/ma-chung-khoan/{SYMBOL}/tinh-hinh-tai-chinh",
            wait_until="networkidle", timeout=60000
        )
        browser.close()

    if token:
        logger.info("Bearer Token captured successfully.")
    else:
        logger.error("Failed to capture Bearer Token.")
    return token


def fetch_report(report_type_id, token):
    """Gọi API Fireant để lấy dữ liệu BCTC"""
    url = f"https://restv2.fireant.vn/symbols/{SYMBOL}/full-financial-reports?type={report_type_id}&year=2024&quarter=4"
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    logger.info(f"Fetching: {url}")
    res = requests.get(url, headers=headers, timeout=20)
    if res.status_code != 200:
        logger.error(f"API returned {res.status_code}: {res.text[:200]}")
        return []
    return res.json()


def dry_run_map(data: list, report_type_str: str):
    """
    Map dữ liệu thô sang Long Format mô phỏng DB schema của Finsang.
    (In ra Terminal - KHÔNG ghi DB)
    """
    logger.info(f"\n{'─'*60}")
    logger.info(f"DRY-RUN MAPPING: {report_type_str} for {SYMBOL}")
    logger.info(f"{'─'*60}")

    rows_preview = []
    for row in data:
        name = str(row.get('name', '')).strip()
        for p_data in row.get('values', []):
            y = p_data.get('year')
            q = p_data.get('quarter')
            val = p_data.get('value', 0)
            period = f"{y}-Q{q}" if q else f"{y}-0"

            # Lọc chỉ 4 quý gần nhất
            if period not in TARGET_PERIODS:
                continue

            rows_preview.append({
                "stock_name": SYMBOL,
                "source": "FIREANT_PDF_TRANS_TEST",
                "period": period,
                "item": name,
                "value_raw": val,
                "value_ty_vnd": round(float(val or 0) / 1_000_000_000, 2)
            })

    # In kết quả ra Terminal
    total = len(rows_preview)
    logger.info(f"Total rows extracted (4 quarters): {total}")

    if rows_preview:
        logger.info("\nSample output (first 15 rows):")
        print("\n{:<10} {:<50} {:>15} {:>15}".format(
            "Period", "Item Name", "Raw Value", "Tỷ VND"
        ))
        print("-" * 95)
        for r in rows_preview[:15]:
            print("{:<10} {:<50} {:>15,} {:>15.2f}".format(
                r['period'],
                r['item'][:50],
                int(r['value_raw'] or 0),
                r['value_ty_vnd']
            ))
        if total > 15:
            print(f"... (and {total - 15} more rows)")

    return rows_preview


def main():
    token = get_bearer_token_simple()
    if not token:
        return

    all_results = {}
    for report_type_str, report_type_id in FIREANT_TYPES.items():
        logger.info(f"\n{'='*60}\nProcessing: {report_type_str}\n{'='*60}")
        data = fetch_report(report_type_id, token)
        if data:
            mapped_rows = dry_run_map(data, report_type_str)
            all_results[report_type_str] = mapped_rows
            logger.info(f"{report_type_str}: ✅ {len(mapped_rows)} rows for {TARGET_PERIODS}")
        else:
            logger.warning(f"{report_type_str}: ⚠️ No data returned")

    # Tổng kết
    print("\n\n" + "═" * 70)
    print("✅  DRY-RUN COMPLETE — NLG PDF_TRANS Pipeline Test Summary")
    print("═" * 70)
    for rtype, rows in all_results.items():
        periods_found = sorted(set(r['period'] for r in rows))
        print(f"  {rtype:<12}: {len(rows):>4} rows | Periods: {periods_found}")
    print("═" * 70)
    print("⚠️  This was a DRY-RUN. No data was written to any database.")
    print("═" * 70)


if __name__ == "__main__":
    main()
