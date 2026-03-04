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
    seen = {}
    for r in res.data:
        seen[r["item_id"]] = r["item"]
    
    with open(output_file, "w", encoding="utf-8") as f:
        for iid in sorted(seen.keys()):
             # Only write if it contains "gửi" or "thanh toán" or "kỳ hạn"
             try:
                 kw = ["gửi", "thanh toán", "kỳ hạn"]
                 if any(k in seen[iid].lower() for k in kw):
                     f.write(f"{iid} | {seen[iid]}\n")
             except:
                 pass

dump_fields("CTG", "balance_sheet", "ctg_bs_fields.txt")
dump_fields("BID", "balance_sheet", "bid_bs_fields.txt")
dump_fields("MBB", "balance_sheet", "mbb_bs_fields.txt")
print("Done dumping fields for CTG, BID, MBB")
