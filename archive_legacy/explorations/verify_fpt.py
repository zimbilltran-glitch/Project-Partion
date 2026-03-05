import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT / "sub-projects" / "Version_2"))

from sb_client import get_sb

# Load env from frontend/.env
load_dotenv(dotenv_path=ROOT / "frontend" / ".env")

# Set required env vars for sb_client
os.environ["SUPABASE_URL"] = os.getenv("VITE_SUPABASE_URL") or ""
os.environ["SUPABASE_KEY"] = os.getenv("VITE_SUPABASE_ANON_KEY") or ""

sb = get_sb()

def check_bank(ticker):
    print(f"\nChecking {ticker} metrics (Source: CFO_CALC_V2)...", flush=True)
    res = sb.table("financial_ratios").select("item_id").eq("stock_name", ticker).eq("source", "CFO_CALC_V2").execute()
    if not res.data:
         print(f"No {ticker} rows found!")
         return
    metrics = set(r["item_id"] for r in res.data)
    print(f"{ticker} metrics found: {len(metrics)}")
    if "bank_4_7" in metrics: print(f"  [OK] {ticker} has CASA (bank_4_7)")
    else: print(f"  [MISSING] {ticker} has NO CASA (bank_4_7)")
    
    if "bank_4_9" in metrics: print(f"  [OK] {ticker} has YOEA (bank_4_9)")
    else: print(f"  [MISSING] {ticker} has NO YOEA (bank_4_9)")

check_bank("ACB")
check_bank("BID")
check_bank("CTG")
check_bank("MBB")
check_bank("HDB")
