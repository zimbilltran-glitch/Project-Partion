import sys, os
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

print("Starting debug_sector.py...", flush=True)

ROOT = Path(__file__).parent.parent.parent
v2_path = ROOT / "sub-projects" / "Version_2"
sys.path.insert(0, str(v2_path))

load_dotenv(dotenv_path=ROOT / "frontend" / ".env")
URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
KEY = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
os.environ["SUPABASE_URL"] = URL
os.environ["SUPABASE_KEY"] = KEY

from sector import get_sector, _CACHE

print("Calling get_sector('ACB')...", flush=True)
try:
    s = get_sector("ACB")
    print(f"Sector for ACB: {s}", flush=True)
    print(f"Cache size: {len(_CACHE)}", flush=True)
except Exception as e:
    print(f"Exception: {e}", flush=True)
