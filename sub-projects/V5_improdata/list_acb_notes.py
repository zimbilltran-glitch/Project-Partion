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

def list_note_fields(ticker):
    print(f"\n--- item_id list for {ticker} in notes ---")
    res = sb.table("notes").select("item_id").eq("stock_name", ticker).execute()
    if not res.data:
        print("No notes found!")
        return
    ids = sorted(list(set(r["item_id"] for r in res.data)))
    for i in ids:
        print(f"  {i}")

list_note_fields("ACB")
