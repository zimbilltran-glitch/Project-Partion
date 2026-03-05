"""
V5 Phase 3 — CORRECTED Spot-check.
The sequential mapping IS correct: bsa{sorted_list[i]} → field[i].
Previous spot-check used WRONG expected keys (old hardcoded values).
This script verifies by reading ACTUAL mapped keys from golden_schema.json.
"""
import json, pandas as pd
from pathlib import Path

BASE = Path(r'd:\Project_partial\Finsang')
V2   = Path(r'd:\Project_partial\Finsang\sub-projects\Version_2')
V5   = Path(r'd:\Project_partial\Finsang\sub-projects\V5_improdata')

# Load schema to get ACTUAL mapped keys
with open(V2 / "golden_schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

field_to_key = {f["field_id"]: f["vietcap_key"] for f in schema["fields"]}

# Load Parquet
bs_pq = pd.read_parquet(BASE / "data" / "financial" / "FPT" / "period_type=year" / "sheet=cdkt" / "FPT.parquet")
is_pq = pd.read_parquet(BASE / "data" / "financial" / "FPT" / "period_type=year" / "sheet=kqkd" / "FPT.parquet")

bs_2024 = bs_pq[bs_pq["period_label"] == "2024"].set_index("field_id")
is_2024 = is_pq[is_pq["period_label"] == "2024"].set_index("field_id")

# Load raw API 2024
with open(V5 / "_raw" / "FPT_BALANCE_SHEET.json", "r", encoding="utf-8") as f:
    raw_bs = json.load(f)
with open(V5 / "_raw" / "FPT_INCOME_STATEMENT.json", "r", encoding="utf-8") as f:
    raw_is = json.load(f)

def get_2024(raw):
    for yr in raw.get("years", []):
        if yr.get("yearReport") == 2024 and yr.get("lengthReport") == 5:
            return yr
    return {}

raw_bs_2024 = get_2024(raw_bs)
raw_is_2024 = get_2024(raw_is)

# ─── Spot check using ACTUAL mapped keys ──────────────────────────────────────
checks = [
    ("CDKT", "cdkt_tong_cong_tai_san", "Tổng cộng tài sản"),
    ("CDKT", "cdkt_tai_san_ngan_han", "TÀI SẢN NGẮN HẠN"),
    ("CDKT", "cdkt_tai_san_dai_han", "TÀI SẢN DÀI HẠN"),
    ("CDKT", "cdkt_no_phai_tra", "NỢ PHẢI TRẢ"),
    ("CDKT", "cdkt_von_chu_so_huu", "VỐN CHỦ SỞ HỮU"),
    ("CDKT", "cdkt_phai_tra_nguoi_ban", "Phải trả người bán"),
    ("CDKT", "cdkt_thue_va_cac_khoan_phai_tra_nha_nuoc", "Thuế & KP trả NN"),
    ("CDKT", "cdkt_tong_cong_nguon_von", "Tổng cộng nguồn vốn"),
    ("KQKD", "kqkd_doanh_thu_thuan", "Doanh thu thuần"),
    ("KQKD", "kqkd_loi_nhuan_gop", "Lợi nhuận gộp"),
    ("KQKD", "kqkd_lai_thuan_sau_thue", "Lãi thuần sau thuế"),
    ("KQKD", "kqkd_loi_nhuan_cua_co_dong_cua_cong_ty_me", "LN cổ đông công ty mẹ"),
]

results = []
results.append(f"{'='*90}")
results.append(f"V5 Spot-Check: Parquet vs Raw API (using corrected key mapping)")
results.append(f"{'='*90}")
results.append(f"{'Status':6s} | {'Label':35s} | {'Mapped Key':12s} | {'Parquet':>22s} | {'API':>22s}")
results.append(f"{'-'*6} | {'-'*35} | {'-'*12} | {'-'*22} | {'-'*22}")

for sheet, field_id, label in checks:
    api_key = field_to_key.get(field_id, "")
    
    if sheet == "CDKT":
        pq_val = float(bs_2024.loc[field_id, "value"]) if field_id in bs_2024.index else None
        api_val = raw_bs_2024.get(api_key) if api_key else None
    else:
        pq_val = float(is_2024.loc[field_id, "value"]) if field_id in is_2024.index else None
        api_val = raw_is_2024.get(api_key) if api_key else None
    
    if pq_val is not None and api_val is not None:
        match = "✅" if abs(pq_val - float(api_val)) < 1 else "❌"
    else:
        match = "⚠️"
    
    results.append(f"{match:6s} | {label:35s} | {api_key:12s} | {pq_val:>22,.0f} | {api_val:>22}")

# ─── Accounting Identity ─────────────────────────────────────────────────────
total_assets = float(bs_2024.loc["cdkt_tong_cong_tai_san", "value"]) if "cdkt_tong_cong_tai_san" in bs_2024.index else 0
total_liab = float(bs_2024.loc["cdkt_no_phai_tra", "value"]) if "cdkt_no_phai_tra" in bs_2024.index else 0
total_equity = float(bs_2024.loc["cdkt_von_chu_so_huu", "value"]) if "cdkt_von_chu_so_huu" in bs_2024.index else 0
tong_nguon_von = float(bs_2024.loc["cdkt_tong_cong_nguon_von", "value"]) if "cdkt_tong_cong_nguon_von" in bs_2024.index else 0

results.append(f"\n{'='*90}")
results.append(f"ACCOUNTING IDENTITY CHECK (FPT 2024)")
results.append(f"{'='*90}")
results.append(f"  Total Assets (cdkt_tong_cong_tai_san):         {total_assets:>25,.0f}")
results.append(f"  Total Liabilities (cdkt_no_phai_tra):           {total_liab:>25,.0f}")
results.append(f"  Total Equity (cdkt_von_chu_so_huu):             {total_equity:>25,.0f}")
results.append(f"  Liab + Equity:                                  {total_liab + total_equity:>25,.0f}")
results.append(f"  Tổng nguồn vốn (cdkt_tong_cong_nguon_von):     {tong_nguon_von:>25,.0f}")

diff = abs(total_assets - tong_nguon_von)
if total_assets > 0:
    pct = diff / total_assets * 100
    verdict = "✅ PASS" if pct < 0.01 else f"❌ FAIL ({pct:.4f}%)"
else:
    verdict = "⚠️ NO DATA"
results.append(f"\n  Assets == Nguồn Vốn?  {verdict}")
results.append(f"  Difference: {diff:,.0f}")

# Also check: Assets = Liabilities + Equity  
diff2 = abs(total_assets - (total_liab + total_equity))
if total_assets > 0:
    pct2 = diff2 / total_assets * 100
    verdict2 = "✅ PASS" if pct2 < 0.01 else f"❌ FAIL ({pct2:.4f}%)"
else:
    verdict2 = "⚠️ NO DATA"
results.append(f"  Assets == Liab + Equity? {verdict2}")

with open(V5 / "_v5_spotcheck.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))
