"""
NLG Data Comparison: Fireant API vs Supabase (KBSV Source)
So sánh số liệu giữa hai nguồn theo từng khoản mục trên cùng kỳ.
"""
import os, sys, json, requests, logging
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SYMBOL = "NLG"
TARGET_PERIODS = ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]
FIREANT_TYPES = {"income_statement": 2, "balance_sheet": 1, "cash_flow": 4}

try:
    from supabase import create_client
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
except Exception as e:
    logger.error(f"Supabase connection failed: {e}")
    sys.exit(1)

# ─── Bước 1: Lấy Bearer Token ─────────────────────────────────────────────
def get_fireant_token():
    from playwright.sync_api import sync_playwright
    token = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        ).new_page()
        def on_req(req):
            nonlocal token
            if not token and "authorization" in req.headers and "Bearer" in req.headers["authorization"]:
                token = req.headers["authorization"]
        page.on("request", on_req)
        page.goto(f"https://fireant.vn/ma-chung-khoan/{SYMBOL}/tinh-hinh-tai-chinh",
                  wait_until="networkidle", timeout=60000)
        browser.close()
    logger.info("Bearer Token captured" if token else "⚠️ Token capture FAILED")
    return token

# ─── Bước 2: Fetch Fireant theo bảng ────────────────────────────────────────
def fetch_fireant(type_id, token):
    url = f"https://restv2.fireant.vn/symbols/{SYMBOL}/full-financial-reports?type={type_id}&year=2024&quarter=4"
    r = requests.get(url, headers={"Authorization": token, "User-Agent": "Mozilla/5.0"}, timeout=20)
    return r.json() if r.status_code == 200 else []

def parse_fireant_to_dict(raw_data):
    """Trả về {(item_name_lower, period): value_ty_vnd}"""
    result = {}
    for row in raw_data:
        name = str(row.get('name', '')).strip().lower()
        for pv in row.get('values', []):
            y, q = pv.get('year'), pv.get('quarter')
            period = f"{y}-Q{q}" if q else f"{y}-0"
            if period not in TARGET_PERIODS:
                continue
            val = float(pv.get('value', 0) or 0)
            result[(name, period)] = round(val / 1_000_000_000, 2)
    return result

# ─── Bước 3: Fetch Supabase ──────────────────────────────────────────────────
def fetch_supabase(table_name):
    """Trả về {(item_lower, period): value}"""
    resp = supabase.table(table_name).select("item, period, value") \
        .eq("stock_name", SYMBOL) \
        .in_("period", TARGET_PERIODS).execute()
    result = {}
    for row in resp.data:
        key = (row['item'].strip().lower(), row['period'])
        result[key] = float(row['value'] or 0)
    return result

# ─── Bước 4: Diff & In Kết quả ──────────────────────────────────────────────
def compare(table_label, fireant_dict, supabase_dict):
    print(f"\n{'═'*100}")
    print(f"  📊  So Sánh: {table_label}  |  NLG  |  FIREANT vs KBSV (Supabase)")
    print(f"{'═'*100}")
    header = f"{'KỲ':<10} {'KHOẢN MỤC':<55} {'FIREANT (Tỷ)':>15} {'KBSV (Tỷ)':>13} {'CHÊNH LỆCH':>12} {'%':>7}"
    print(header)
    print(f"{'─'*100}")

    all_keys = sorted(set(list(fireant_dict.keys()) + list(supabase_dict.keys())), key=lambda x: x[1])
    matched = 0; unmatched = 0; missing = 0
    diff_rows = []
    
    for key in all_keys:
        name, period = key
        fa_val = fireant_dict.get(key)
        sb_val = supabase_dict.get(key)
        
        if fa_val is None or sb_val is None:
            missing += 1
            status = "⚠️ chỉ có 1 nguồn"
            diff_rows.append((period, name[:52], fa_val or "—", sb_val or "—", "N/A", status))
            continue
        
        diff = fa_val - sb_val
        pct  = (abs(diff) / abs(sb_val) * 100) if sb_val != 0 else 0
        
        if pct > 1:
            flag = f"❌ {pct:.1f}%"
            unmatched += 1
        elif pct > 0:
            flag = f"⚠️ {pct:.2f}%"
            matched += 1
        else:
            flag = "✅ MATCH"
            matched += 1
        diff_rows.append((period, name[:52], fa_val, sb_val, diff, flag))
    
    for r in diff_rows:
        period, name, fa, sb, diff, flag = r
        if isinstance(fa, str) or isinstance(sb, str):
            print(f"{period:<10} {name:<55} {'—':>15} {'—':>13} {'—':>12} {flag}")
        else:
            print(f"{period:<10} {name:<55} {fa:>15,.2f} {sb:>13,.2f} {diff:>+12,.2f} {flag}")

    print(f"\n  ✅ Khớp / Gần khớp (<1%): {matched}   |   ❌ Sai lệch >1%: {unmatched}   |   ⚠️ Chỉ 1 nguồn: {missing}")


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    token = get_fireant_token()
    if not token:
        return

    for table_name, type_id in FIREANT_TYPES.items():
        logger.info(f"Processing {table_name}...")
        raw = fetch_fireant(type_id, token)
        fa_data = parse_fireant_to_dict(raw)
        sb_data = fetch_supabase(table_name)
        compare(table_name.upper(), fa_data, sb_data)

    print(f"\n{'═'*100}")
    print("  Xong. Không có dữ liệu nào bị ghi vào DB trong quá trình so sánh này.")
    print(f"{'═'*100}\n")

if __name__ == "__main__":
    main()
