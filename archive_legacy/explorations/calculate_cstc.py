import pandas as pd
import io
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

import sys
sys.stdout.reconfigure(encoding='utf-8')

# Define paths
ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data" / "financial"
ENV_PATH = ROOT / "frontend" / ".env"

# Load Supabase credentials
load_dotenv(dotenv_path=ENV_PATH)
URL = os.getenv("VITE_SUPABASE_URL")
KEY = os.getenv("VITE_SUPABASE_ANON_KEY")

os.environ["SUPABASE_URL"] = URL
os.environ["SUPABASE_KEY"] = KEY

if not URL or not KEY:
    print("Critical: Supabase URL or KEY missing from frontend/.env")
    sys.exit(1)

sb = create_client(URL, KEY)

def get_parquet_df(ticker, sheet_id, period_type="year"):
    """Loads decrypted Parquet data for a sheet."""
    pq_path = DATA_DIR / ticker.upper() / f"period_type={period_type}" / f"sheet={sheet_id.lower()}" / f"{ticker.upper()}.parquet"
    if not pq_path.exists():
        print(f"Missing Parquet: {pq_path}")
        return None
    # Assuming no encryption for this quick script, adjust if security.py is needed
    try:
        from security import get_cipher
        cipher = get_cipher()
        if cipher:
            with open(pq_path, "rb") as f:
                decrypted = cipher.decrypt(f.read())
            return pd.read_parquet(io.BytesIO(decrypted))
    except Exception as e:
        print(f"Decryption failed for {pq_path}: {e}")
    
    try:
        return pd.read_parquet(pq_path)
    except Exception as e:
        print(f"Read parquet directly failed for {pq_path}: {e}")
        return None
def calculate_ratios(ticker):
    print(f"Calculating Financial Ratios (CSTC) for {ticker}...")
    
    ratio_defs = {
        "cstc_current_ratio": "Hệ số thanh toán hiện hành (Current Ratio)",
        "cstc_quick_ratio": "Hệ số thanh toán nhanh (Quick Ratio)",
        "cstc_debt_to_equity": "Nợ phải trả / Vốn chủ sở hữu (D/E)",
        "cstc_roe": "Tỷ suất LNST trên VCSH (ROE)",
        "cstc_roa": "Tỷ suất LNST trên Tổng CS (ROA)",
        "cstc_gross_margin": "Biên lợi nhuận gộp",
        "cstc_net_margin": "Biên lợi nhuận ròng"
    }

    payloads = []

    from sector import get_sector
    
    for pt in ["year", "quarter"]:
        sector = get_sector(ticker)
        sheet_bs = "cdkt" if sector == "normal" else f"cdkt_{sector}"
        sheet_is = "kqkd" if sector == "normal" else f"kqkd_{sector}"
        
        bs_df = get_parquet_df(ticker, sheet_bs, pt)
        is_df = get_parquet_df(ticker, sheet_is, pt)
        
        if bs_df is None or is_df is None:
            print(f"Skipping {pt} for {ticker} - missing data")
            continue
            
        all_periods = set(bs_df["period_label"].unique()).intersection(set(is_df["period_label"].unique()))
        
        for p in all_periods:
            # Get specific period data
            bs_p = bs_df[bs_df["period_label"] == p].set_index("field_id")["value"]
            is_p = is_df[is_df["period_label"] == p].set_index("field_id")["value"]
            
            # Safe extraction helper
            def val(df, key): return float(df.get(key, 0) or 0)
            
            # Balance Sheet metrics
            # Normal
            current_assets = val(bs_p, "cdkt_tai_san_ngan_han")
            inventory = val(bs_p, "cdkt_hang_ton_kho")
            current_liab = val(bs_p, "cdkt_no_ngan_han")
            total_liab = val(bs_p, "cdkt_no_phai_tra") or val(bs_p, "cdkt_bank_no_phai_tra") or val(bs_p, "cdkt_sec_no_phai_tra")
            total_equity = val(bs_p, "cdkt_von_chu_so_huu") or val(bs_p, "cdkt_bank_von_chu_so_huu") or val(bs_p, "cdkt_sec_von_chu_so_huu_1") or val(bs_p, "cdkt_sec_von_chu_so_huu")
            total_assets = val(bs_p, "cdkt_tong_cong_tai_san") or val(bs_p, "cdkt_bank_tong_cong_tai_san") or val(bs_p, "cdkt_sec_tong_tai_san")
            
            # Income Statement metrics
            net_revenue = val(is_p, "kqkd_doanh_thu_thuan") or val(is_p, "kqkd_sec_doanh_thu_hoat_dong") or val(is_p, "kqkd_bank_thu_nhap_lai_thuan")
            gross_profit = val(is_p, "kqkd_loi_nhuan_gop")
            net_income = val(is_p, "kqkd_loi_nhuan_cua_co_dong_cua_cong_ty_me") or val(is_p, "kqkd_bank_co_dong_cua_cong_ty_me") or val(is_p, "kqkd_sec_loi_nhuan_sau_thue_phan_bo_cho_chu_so_huu")
            
            # Calculate values
            vals = {
                "cstc_current_ratio": round(current_assets / current_liab, 2) if current_liab > 0 else None,
                "cstc_quick_ratio": round((current_assets - inventory) / current_liab, 2) if current_liab > 0 else None,
                "cstc_debt_to_equity": round(total_liab / total_equity, 2) if total_equity > 0 else None,
                "cstc_roe": round((net_income / total_equity) * 100, 2) if total_equity > 0 else None,
                "cstc_roa": round((net_income / total_assets) * 100, 2) if total_assets > 0 else None,
                "cstc_gross_margin": round((gross_profit / net_revenue) * 100, 2) if net_revenue > 0 else None,
                "cstc_net_margin": round((net_income / net_revenue) * 100, 2) if net_revenue > 0 else None
            }
            
            for key, name in ratio_defs.items():
                if vals[key] is not None:
                    payloads.append({
                        "stock_name": ticker,
                        "asset_type": "STOCK",
                        "ratio_name": name,
                        "item_id": key,
                        "period": p,
                        "value": vals[key],
                        "source": "CFO_CALC_V2"
                    })

    # Upsert to Supabase
    print("Pushing calculations to Supabase...")
    try:
        # Delete old data
        sb.table("financial_ratios").delete().eq("stock_name", ticker).eq("source", "CFO_CALC_V2").execute()
        # Batch insert new data
        if payloads:
            # Supabase free tier limits payload size, chunking to chunks of 100
            for i in range(0, len(payloads), 100):
                sb.table("financial_ratios").insert(payloads[i:i+100]).execute()
    except Exception as e:
        print(f"Error upserting data: {e}")
            
    print(f"Successfully calculated and pushed CSTC for {ticker}.")

if __name__ == "__main__":
    TICKERS = [
        'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
        'MBB', 'MSN', 'MWG', 'PLX', 'POW', 'SAB', 'SHB', 'SSB', 'SSI', 'STB',
        'TCB', 'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB', 'VRE'
    ]
    for t in TICKERS:
        calculate_ratios(t)
