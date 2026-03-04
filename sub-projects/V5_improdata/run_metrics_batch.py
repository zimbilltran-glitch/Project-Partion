"""
Phase 5 Fix: Batch run metrics.py for all VN30 tickers.
Standalone script with explicit logging and flush.
"""
import os, sys, math
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

print("Starting run_metrics_batch.py...", flush=True)

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "sub-projects" / "Version_2"))

# Load env
print("Loading environment...", flush=True)
load_dotenv(dotenv_path=ROOT / "frontend" / ".env")
URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
KEY = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
os.environ["SUPABASE_URL"] = URL
os.environ["SUPABASE_KEY"] = KEY

if not URL or not KEY:
    print("Critical: Supabase URL/KEY missing!", flush=True)
    sys.exit(1)

print(f"Supabase URL: {URL[:20]}...", flush=True)

from sb_client import get_sb
sb = get_sb()

print("Importing metrics_debug.py...", flush=True)
from metrics_debug import calc_metrics

TICKERS = [
    'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
    'MBB', 'MSN', 'MWG', 'PLX', 'POW', 'SAB', 'SHB', 'SSB', 'SSI', 'STB',
    'TCB', 'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB', 'VRE'
]

def build_ratio_rows(df, ticker, period_type):
    """Transform metrics DataFrame into financial_ratios rows."""
    rows = []
    meta_cols = ("item_id", "vn_name", "unit", "level", "row_number")
    period_cols = [c for c in df.columns if c not in meta_cols]

    for _, row in df.iterrows():
        ratio_name = str(row.get("vn_name", ""))
        item_id = str(row.get("item_id", ""))
        unit = str(row.get("unit", ""))
        level = int(row.get("level", 0))
        row_num = int(row.get("row_number", 0))

        for period_col in period_cols:
            val = row.get(period_col)
            if val is None or pd.isna(val):
                continue
            try:
                numeric_val = float(val)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(numeric_val):
                continue

            rows.append({
                "stock_name": ticker.upper(),
                "asset_type": "STOCK",
                "ratio_name": ratio_name,
                "period":     period_col,
                "value":      numeric_val,
                "source":     "CFO_CALC_V2",
                "item_id":    item_id,
                "levels":     level,
                "row_number": row_num,
                "unit":       unit,
            })
    return rows

def process_ticker(ticker):
    print(f"\n{'='*60}", flush=True)
    print(f"  Processing: {ticker}", flush=True)
    print(f"{'='*60}", flush=True)
    
    # Delete old ratios for this ticker
    try:
        print(f"  Deleting old ratios for {ticker}...", flush=True)
        sb.table("financial_ratios").delete().eq("stock_name", ticker).execute()
        print(f"  ✅ Cleared old ratios", flush=True)
    except Exception as e:
        print(f"  ⚠️ Warning: Could not clear old ratios: {e}", flush=True)

    for period in ["year", "quarter"]:
        try:
            print(f"  Calculating {period} metrics via metrics.calc_metrics()...", flush=True)
            df = calc_metrics(ticker, period)
            if df.empty:
                print(f"  ⚠️ No metrics data for {ticker} ({period})", flush=True)
                continue

            rows = build_ratio_rows(df, ticker, period)
            if not rows:
                print(f"  ⚠️ No rows to upload for {ticker} ({period})", flush=True)
                continue

            # Chunk upsert (100 rows at a time)
            print(f"  Upserting {len(rows)} rows to Supabase...", flush=True)
            total = 0
            for i in range(0, len(rows), 100):
                chunk = rows[i:i+100]
                sb.table("financial_ratios").upsert(chunk).execute()
                total += len(chunk)

            print(f"  ✅ Uploaded {total} ratio rows for {ticker} ({period})", flush=True)
        except Exception as e:
            print(f"  ❌ Error for {ticker} ({period}): {e}", flush=True)

if __name__ == "__main__":
    print("Starting VN30 Metrics Re-Sync...", flush=True)
    print(f"Tickers: {len(TICKERS)}", flush=True)

    for t in TICKERS:
        process_ticker(t)

    print("\n🎯 Done! All tickers processed.", flush=True)
