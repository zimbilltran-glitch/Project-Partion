import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Path setup
ROOT = Path(__file__).parent.parent.parent
load_dotenv(dotenv_path=ROOT / ".env")

TICKERS_RAW = os.getenv("FINSANG_TICKERS", "")
TICKERS = [t.strip() for t in TICKERS_RAW.split(",") if t.strip()]

def run_cmd(cmd, cwd=None):
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result

def main():
    if not TICKERS:
        print("No tickers found in .env")
        return

    print(f"Starting Full Resync for {len(TICKERS)} tickers...")
    
    # 0. Purge from Supabase
    print("Purging existing financial data from Supabase for target tickers...")
    ticker_list_sql = ", ".join([f"'{t}'" for t in TICKERS])
    purge_sql = f"""
    DELETE FROM balance_sheet WHERE stock_name IN ({ticker_list_sql});
    DELETE FROM income_statement WHERE stock_name IN ({ticker_list_sql});
    DELETE FROM cash_flow WHERE stock_name IN ({ticker_list_sql});
    DELETE FROM financial_ratios WHERE stock_name IN ({ticker_list_sql});
    """
    
    # We use execute_sql tool via subprocess or just rely on sync_supabase purging.
    # Actually sync_supabase.py ALREADY purges by ticker if we call it correctly.
    # But doing a bulk delete is faster.
    
    # Let's just run the pipeline and let sync_supabase handle the per-ticker purge 
    # as it's already implemented there and safer.
    
    # 1. Pipeline for each ticker
    for i, ticker in enumerate(TICKERS):
        print(f"[{i+1}/{len(TICKERS)}] Processing {ticker}...")
        run_cmd(["python", "pipeline.py", "--ticker", ticker], cwd=Path(__file__).parent)

    # 2. Sync all to Supabase
    print("Syncing all Parquet data to Supabase...")
    run_cmd(["python", "sync_supabase.py", "--all"], cwd=Path(__file__).parent)

    print("Full Resync Complete!")

if __name__ == "__main__":
    main()
