"""
V6 Smoke Test — Production Readiness Check
============================================
Tests the V6 pipeline setup without writing to DB or downloading new files.
Run before every deployment or after schema changes.

Usage:
    python smoke_test.py              # Full smoke test
    python smoke_test.py --quick      # Import + config checks only

Exit code: 0 = PASS, 1 = FAIL
"""

import sys
import os
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("SmokeTest")

ROOT = Path(__file__).parent.parent.parent
V6_DIR = Path(__file__).parent
RESULTS = {"passed": [], "failed": [], "warnings": []}


def check(name: str, condition: bool, msg: str = "", warning: bool = False):
    if condition:
        log.info(f"  ✅ PASS: {name}")
        RESULTS["passed"].append(name)
    else:
        level = "warnings" if warning else "failed"
        marker = "⚠️  WARN" if warning else "  ❌ FAIL"
        log.warning(f"{marker}: {name} — {msg}")
        RESULTS[level].append(f"{name}: {msg}")


# ── Test 1: Environment Variables ─────────────────────────
log.info("\n[Test 1] Environment Variables")
from dotenv import load_dotenv
load_dotenv(dotenv_path=ROOT / "frontend" / ".env")
URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
KEY = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
check("SUPABASE_URL set",       bool(URL), "VITE_SUPABASE_URL or SUPABASE_URL not found in .env")
check("SUPABASE_KEY set",       bool(KEY), "VITE_SUPABASE_ANON_KEY or SUPABASE_KEY not found in .env")
check("ENCRYPTION_KEY set",
      bool(os.getenv("FINSANG_ENCRYPTION_KEY")),
      "FINSANG_ENCRYPTION_KEY missing — encrypted Parquet won't work",
      warning=True)

# ── Test 2: Module Imports ────────────────────────────────
log.info("\n[Test 2] Module Imports")
sys.path.insert(0, str(ROOT / "sub-projects" / "V2_Data_Pipeline"))
if URL: os.environ["SUPABASE_URL"] = URL
if KEY: os.environ["SUPABASE_KEY"] = KEY

try:
    from sb_client import get_sb
    check("sb_client import",   True)
except Exception as e:
    check("sb_client import",   False, str(e))

try:
    from sector import get_sector
    check("sector import",      True)
    check("sector MBB=bank",    get_sector("MBB") == "bank", f"Expected 'bank', got '{get_sector('MBB')}'")
    check("sector SSI=sec",     get_sector("SSI") == "sec",  f"Expected 'sec', got '{get_sector('SSI')}'")
    check("sector FPT=normal",  get_sector("FPT") == "normal", f"Expected 'normal', got '{get_sector('FPT')}'")
except Exception as e:
    check("sector import",      False, str(e))

try:
    from excel_data_auditor import read_excel_with_timeout, EXCEL_READ_TIMEOUT
    check("auditor import",         True)
    check("timeout guard exists",   EXCEL_READ_TIMEOUT == 90, f"Expected 90s, got {EXCEL_READ_TIMEOUT}s")
except Exception as e:
    check("auditor import",         False, str(e))

# ── Test 3: Config Files ──────────────────────────────────
log.info("\n[Test 3] Config Files")
v2 = ROOT / "sub-projects" / "V2_Data_Pipeline"
check("lite_schema.json exists",   (v2 / "lite_schema.json").exists(),   "lite_schema.json not found")
check("golden_schema.json exists", (v2 / "golden_schema.json").exists(), "golden_schema.json not found")
check("v6_pending_audits.json",    (V6_DIR / "v6_pending_audits.json").exists(), "pending audits file missing")

try:
    with open(v2 / "lite_schema.json") as f:
        schema = json.load(f)
    check("lite_schema valid JSON",  True)
    check("lite_schema has fields",  len(schema.get("fields", [])) > 100,
          f"Only {len(schema.get('fields', []))} fields — expected 100+")
except Exception as e:
    check("lite_schema valid JSON",  False, str(e))

# ── Test 4: Supabase Connectivity ────────────────────────
log.info("\n[Test 4] Supabase Connectivity (live ping)")
try:
    sb = get_sb()
    res = sb.table("financial_ratios").select("stock_name").limit(1).execute()
    check("Supabase SELECT financial_ratios", bool(res.data), "No data returned — table empty or connection failed")
    res2 = sb.table("financial_ratios_wide").select("stock_name").limit(1).execute()
    check("Supabase SELECT financial_ratios_wide", bool(res2.data), "View returned no data")
except Exception as e:
    check("Supabase connectivity",   False, str(e))

# ── Test 5: Excel Download Dir ────────────────────────────
log.info("\n[Test 5] File System")
excel_dir = ROOT / "data" / "excel_imports"
check("excel_imports dir exists", excel_dir.exists(), "data/excel_imports/ not found — create it before running pipeline")
if excel_dir.exists():
    xlsx_files = list(excel_dir.glob("*.xlsx"))
    check("Excel files present", len(xlsx_files) > 0, "No .xlsx files in data/excel_imports/", warning=True)

# ── Results ───────────────────────────────────────────────
log.info("\n" + "="*50)
log.info(f"SMOKE TEST RESULTS:")
log.info(f"  ✅ PASSED:   {len(RESULTS['passed'])}")
log.info(f"  ⚠️  WARNINGS: {len(RESULTS['warnings'])}")
log.info(f"  ❌ FAILED:   {len(RESULTS['failed'])}")
log.info("="*50)

if RESULTS["failed"]:
    log.error("SMOKE TEST FAILED. Fix the issues above before running pipeline.")
    sys.exit(1)
else:
    log.info("SMOKE TEST PASSED ✅")
    sys.exit(0)
