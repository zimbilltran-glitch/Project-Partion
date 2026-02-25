"""
VIC Data Comparison: Fireant API (8 quarters 2024-2025)
Fetch KQKD, CDKT, LCTT cho VIC — KHÔNG ghi DB — in ra Terminal để đối chiếu tay với Web.
"""
import os, sys, json, requests, logging
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SYMBOL = "VIC"
# 8 quý: 2024-Q1 → 2025-Q4
TARGET_PERIODS = [
    "2024-Q1","2024-Q2","2024-Q3","2024-Q4",
    "2025-Q1","2025-Q2","2025-Q3","2025-Q4"
]
FIREANT_TYPES = {"KQKD": 2, "CDKT": 1, "LCTT_GT": 4}

# ─── Bearer Token ────────────────────────────────────────────────────────────
def get_token():
    from playwright.sync_api import sync_playwright
    token = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)").new_page()
        def on_req(req):
            nonlocal token
            if not token and "authorization" in req.headers and "Bearer" in req.headers["authorization"]:
                token = req.headers["authorization"]
        page.on("request", on_req)
        page.goto(f"https://fireant.vn/ma-chung-khoan/{SYMBOL}/tinh-hinh-tai-chinh",
                  wait_until="networkidle", timeout=60000)
        browser.close()
    logger.info("✅ Token captured" if token else "❌ Token capture FAILED")
    return token

# ─── Fetch API ────────────────────────────────────────────────────────────────
def fetch_api(type_id, token):
    # year=2025, quarter=4 → Fireant sẽ trả về các quý gần về trước
    url = f"https://restv2.fireant.vn/symbols/{SYMBOL}/full-financial-reports?type={type_id}&year=2025&quarter=4"
    r = requests.get(url, headers={"Authorization": token, "User-Agent": "Mozilla/5.0"}, timeout=20)
    if r.status_code != 200:
        logger.error(f"API error {r.status_code}: {r.text[:200]}")
        return []
    return r.json()

# ─── Parse sang Long Format ───────────────────────────────────────────────────
def parse(raw_data):
    """Trả về dict: {(item_name, period): value_ty_vnd}"""
    result = {}
    for row in raw_data:
        name = str(row.get('name', '')).strip()
        for pv in row.get('values', []):
            y, q = pv.get('year'), pv.get('quarter')
            period = f"{y}-Q{q}" if q else f"{y}-0"
            if period not in TARGET_PERIODS:
                continue
            val = float(pv.get('value', 0) or 0)
            result[(name, period)] = round(val / 1_000_000_000, 2)
    return result

# ─── In bảng đối chiếu ────────────────────────────────────────────────────────
def print_table(label, data_dict):
    print(f"\n{'═'*120}")
    print(f"  📊  {SYMBOL} — {label} — Fireant API (8 Quý 2024–2025)")
    print(f"{'═'*120}")

    # Nhóm items theo tên
    items = {}
    for (name, period), val in data_dict.items():
        if name not in items:
            items[name] = {}
        items[name][period] = val

    if not items:
        print("  ⚠️  Không có dữ liệu.")
        return

    # Header row
    avail_periods = [p for p in TARGET_PERIODS if any(p in d for d in items.values())]
    header = f"{'KHOẢN MỤC':<60}" + "".join(f"{p:>13}" for p in avail_periods)
    print(header)
    print("─" * 120)

    for name, period_vals in items.items():
        row = f"{name[:58]:<60}"
        for p in avail_periods:
            v = period_vals.get(p, "—")
            if v == "—":
                row += f"{'—':>13}"
            else:
                row += f"{v:>13,.2f}"
        print(row)

    print(f"\n  Tổng số chỉ tiêu: {len(items)} | Các kỳ có dữ liệu: {avail_periods}")

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    token = get_token()
    if not token:
        return

    for label, type_id in FIREANT_TYPES.items():
        logger.info(f"Fetching {label}...")
        raw = fetch_api(type_id, token)
        data = parse(raw)
        print_table(label, data)

    print(f"\n{'═'*120}")
    print("  Xong. KHÔNG có dữ liệu nào được ghi vào DB.")
    print(f"{'═'*120}\n")

if __name__ == "__main__":
    main()
