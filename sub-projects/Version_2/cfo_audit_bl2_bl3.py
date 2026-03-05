"""
CFO Audit Script - Resolves BL-2 and BL-3
Checks:
1. BL-2: Accounting Identity (Assets = Liabilities + Equity) for all VN30, across all sectors.
2. BL-3: Cash Flow Identity (Net CF = Op CF + Inv CF + Fin CF) for all VN30.
"""

import os, sys
from pathlib import Path

V2 = Path(r'd:\Project_partial\Finsang\sub-projects\Version_2')
sys.path.insert(0, str(V2))

from sync_supabase import get_supabase

VN30 = [
    "FPT", "VNM", "VCB", "VHM", "HPG",
    "MBB", "TCB", "VPB", "BID", "CTG",
    "SSI", "HCM", "VCI", "VND", "SHS",
    "MSN", "MWG", "VRE", "PLX", "GAS",
    "SAB", "ACB", "STB", "TPB", "SHB",
    "POW", "BCM", "GVR", "PDR", "KDH",
]

# Definition of Accounting Identity (BL-2)
ASSET_CHECKS = {
    "normal": {
        "asset": "cdkt_tong_cong_tai_san",
        "liab": "cdkt_no_phai_tra",
        "eq": "cdkt_von_chu_so_huu"
    },
    "bank": {
        "asset": "cdkt_bank_tong_tai_san",
        "liab": "cdkt_bank_tong_no_phai_tra",
        "eq": "cdkt_bank_von_chu_so_huu"
    },
    "sec": {
        "asset": "cdkt_sec_tong_cong_tai_san",
        "liab": "cdkt_sec_no_phai_tra",
        "eq": "cdkt_sec_von_chu_so_huu"
    }
}

# Definition of CF Identity (BL-3)
CF_CHECKS = {
    "normal": {
        "net": "lctt_luu_chuyen_tien_thuan_trong_ky",
        "op": "lctt_luu_chuyen_tien_te_rong_tu_cac_hoat_dong_san_xuat_kinh_",
        "inv": "lctt_luu_chuyen_tien_thuan_tu_hoat_dong_dau_tu",
        "fin": "lctt_luu_chuyen_tien_thuan_tu_hoat_dong_tai_chinh",
    },
    "bank": {
        "net": "lctt_bank_luu_chuyen_tien_thuan_trong_ky",
        "op": "lctt_bank_luu_chuyen_tien_thuan_tu_cac_hoat_dong_san_xuat_kinh_do",
        "inv": "lctt_bank_luu_chuyen_tien_thuan_tu_hoat_dong_dau_tu",
        "fin": "lctt_bank_luu_chuyen_tien_thuan_tu_hoat_dong_tai_chinh"
    },
    "sec": {
        "net": "lctt_sec_luu_chuyen_tien_thuan_trong_ky",
        "op": "lctt_sec_luu_chuyen_thuan_tu_hoat_dong_kinh_doanh",
        "inv": "lctt_sec_luu_chuyen_tien_thuan_tu_hoat_dong_dau_tu",
        "fin": "lctt_sec_luu_chuyen_thuan_tu_hoat_dong_tai_chinh",
    }
}

def do_audit(sb, ticker, period="2024"):
    # 1. Fetch from Supabase
    bs_data = sb.table("balance_sheet").select("*").eq("stock_name", ticker).eq("period", period).execute().data
    cf_data = sb.table("cash_flow").select("*").eq("stock_name", ticker).eq("period", period).execute().data
    
    bs_dict = {r["item_id"]: r["value"] for r in bs_data} if bs_data else {}
    cf_dict = {r["item_id"]: r["value"] for r in cf_data} if cf_data else {}
    
    if not bs_dict or not cf_dict:
        return f"Fail (No data in DB for {period})"

    # Detect sector
    sector = None
    if "cdkt_tong_cong_tai_san" in bs_dict: sector = "normal"
    elif "cdkt_bank_tong_tai_san" in bs_dict: sector = "bank"
    elif "cdkt_sec_tong_cong_tai_san" in bs_dict: sector = "sec"
    else: return "Fail (Unknown sector)"

    # BL-2 Check
    acct = ASSET_CHECKS[sector]
    t_asset = bs_dict.get(acct["asset"], 0)
    t_liab = bs_dict.get(acct["liab"], 0)
    t_eq = bs_dict.get(acct["eq"], 0)
    diff_bs = abs(t_asset - (t_liab + t_eq))
    bs_ok = diff_bs < 1000 # Allow small float diffs

    # BL-3 Check
    cf = CF_CHECKS[sector]
    t_net = cf_dict.get(cf["net"], 0)
    t_op = cf_dict.get(cf["op"], 0)
    t_inv = cf_dict.get(cf["inv"], 0)
    t_fin = cf_dict.get(cf["fin"], 0) if cf["fin"] else 0
    diff_cf = abs(t_net - (t_op + t_inv + t_fin))
    cf_ok = diff_cf < 1000
    
    if bs_ok and cf_ok:
        return f"PASS ({sector.upper():6}) | BS Diff: {diff_bs:,.0f} | CF Diff: {diff_cf:,.0f}"
    else:
        errs = []
        if not bs_ok: errs.append(f"BS_FAIL(Diff={diff_bs:,.0f})")
        if not cf_ok: errs.append(f"CF_FAIL(Diff={diff_cf:,.0f}, net={t_net}, op={t_op}, inv={t_inv}, fin={t_fin})")
        return f"ERROR ({sector.upper():6}) | {' & '.join(errs)}"

def main():
    sb = get_supabase()
    results = {}
    print(f"\n{'='*70}\n  CFO AUDIT TOOL: BALANCE SHEET & CASH FLOW CHECKS (VN30)\n{'='*70}\n")
    for t in VN30:
        results[t] = do_audit(sb, t)
        print(f"  {t:5}: {results[t]}")

if __name__ == "__main__":
    main()
