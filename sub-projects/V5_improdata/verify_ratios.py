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

def verify_ratios(ticker):
    print(f"\n--- Verifying ratios for {ticker} ---")
    res = sb.table("financial_ratios").select("item_id").eq("stock_name", ticker).execute()
    ids = list(set(r["item_id"] for r in res.data))
    print(f"Total unique metrics: {len(ids)}")
    if len(ids) > 20:
        print("✅ Success: Metrics restored (found > 20 items)")
    else:
        print(f"❌ Failed: Still found only {len(ids)} items")

verify_ratios("ACB")
verify_ratios("BID")
