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

def inspect_row(table):
    print(f"\n--- Row keys for {table} ---")
    res = sb.table(table).select("*").limit(1).execute()
    if res.data:
        print(f"Keys: {list(res.data[0].keys())}")
        print(f"Sample data: {res.data[0]}")
    else:
        print("No data found!")

inspect_row("balance_sheet")
inspect_row("income_statement")
