import os
import sys
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# Add Version_2 to path
ROOT = Path(__file__).parent.parent.parent
v2_path = ROOT / "sub-projects" / "Version_2"
sys.path.insert(0, str(v2_path))

from metrics import calc_metrics
from sync_supabase import build_ratio_rows, SHEET_TO_TABLE
import supabase

load_dotenv(dotenv_path=ROOT / "frontend" / ".env")

# Map VITE_ env vars for compatibility
URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
KEY = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
os.environ["SUPABASE_URL"] = URL
os.environ["SUPABASE_KEY"] = KEY

TICKERS = ["ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG", 
           "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB", 
           "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE"]

sb = supabase.create_client(URL, KEY)

def re_sync_ticker(ticker):
    print(f"🔄 Processing Ratios for {ticker}...")
    try:
        sb.table("financial_ratios").delete().eq("stock_name", ticker).execute()
        print(f"  🗑️ Cleared old ratios for {ticker}")
    except Exception as e:
        print(f"  ⚠️ Could not clear old ratios: {e}")
        
    for period in ["year", "quarter"]:
        try:
            df = calc_metrics(ticker, period)
            if df.empty:
                print(f"  ⚠️ No metrics data for {ticker} ({period})")
                continue
            
            rows = build_ratio_rows(df, ticker, period)
            if not rows:
                continue
                
            # Upsert to handle existing rows
            res = sb.table("financial_ratios").upsert(rows).execute()
            print(f"  ✅ Uploaded {len(rows)} ratio rows for {ticker} ({period})")
        except Exception as e:
            print(f"  ❌ Error for {ticker} ({period}): {e}")

if __name__ == "__main__":
    print("🚀 Starting CSTC Hierarchy Re-Sync...")
    for ticker in TICKERS:
        re_sync_ticker(ticker)
    print("🎯 Re-Sync Complete!")
