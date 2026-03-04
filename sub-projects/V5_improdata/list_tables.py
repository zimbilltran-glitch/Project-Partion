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

res = sb.rpc("get_tables").execute() # This might not work if RPC not defined
if not res.data:
    # Try a simple query to information_schema if allowed (usually not via REST)
    # Let's just try to guess or search for more SHEET_TO_TABLE in pipeline.py
    print("Could not list tables via RPC.")
