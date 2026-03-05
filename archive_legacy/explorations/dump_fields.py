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

def dump_fields(ticker, table, output_file):
    res = sb.table(table).select("item_id, item").eq("stock_name", ticker).execute()
    # item is the vn_name
    seen = {}
    for r in res.data:
        seen[r["item_id"]] = r["item"]
    
    with open(output_file, "w", encoding="utf-8") as f:
        for iid in sorted(seen.keys()):
            f.write(f"{iid} | {seen[iid]}\n")

dump_fields("ACB", "balance_sheet", "acb_bs_fields.txt")
dump_fields("ACB", "income_statement", "acb_is_fields.txt")
print("Done dumping fields to acb_bs_fields.txt and acb_is_fields.txt")
