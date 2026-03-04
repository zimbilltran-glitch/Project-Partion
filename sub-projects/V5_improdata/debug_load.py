import sys, os
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

print("Starting debug_load.py...", flush=True)

ROOT = Path(__file__).parent.parent.parent
v2_path = ROOT / "sub-projects" / "Version_2"
sys.path.insert(0, str(v2_path))

load_dotenv(dotenv_path=ROOT / "frontend" / ".env")
URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
KEY = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
os.environ["SUPABASE_URL"] = URL
os.environ["SUPABASE_KEY"] = KEY

print(f"URL: {URL[:20]}...", flush=True)

from pipeline import load_tab_from_supabase

# Testing ACB
ticker = "ACB"
period = "year"
sheet = "cdkt_bank"

print(f"Calling load_tab_from_supabase({ticker}, {period}, {sheet})...", flush=True)
try:
    df = load_tab_from_supabase(ticker, period, sheet)
    print(f"Success! DF shape: {df.shape}", flush=True)
    if not df.empty:
        print(f"Columns: {df.columns.tolist()}", flush=True)
except Exception as e:
    print(f"Exception: {e}", flush=True)
