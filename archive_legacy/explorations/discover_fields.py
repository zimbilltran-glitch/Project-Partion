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

def list_fields(ticker, table):
    print(f"\n--- item_id list for {ticker} in {table} ---")
    res = sb.table(table).select("item_id").eq("stock_name", ticker).execute()
    ids = sorted(list(set(r["item_id"] for r in res.data)))
    for i in ids:
        # Check if it contains keywords "gửi" or "thanh toán" by looking up the name internally
        # but don't print the name to avoid Unicode error
        print(f"  {i}")

list_fields("ACB", "balance_sheet")
list_fields("ACB", "income_statement")
