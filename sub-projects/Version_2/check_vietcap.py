import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")
from pipeline import load_schema
from providers.vietcap import VietcapProvider

provider = VietcapProvider()
mb = provider.fetch_section("MBB", "BALANCE_SHEET")

# Get one year, say 2024
mb_yr = [row for row in mb.get("years", []) if row.get("yearReport") == 2024]
if mb_yr:
    print("MBB (Bank, CDKT) raw keys:")
    keys = sorted([k for k in mb_yr[0].keys() if k.startswith("bsa")])
    print(f"Total bsa fields: {len(keys)}")
    
    # Are values completely null?
    non_nulls = {k: v for k, v in mb_yr[0].items() if v is not None and k.startswith("bsa") and v != 0}
    print(f"Non-null/zero bsa fields: {len(non_nulls)}")
    print(f"Sample: {list(non_nulls.items())[:5]}")

# Check HPG
hpg = provider.fetch_section("HPG", "BALANCE_SHEET")
hpg_yr = [row for row in hpg.get("years", []) if row.get("yearReport") == 2024]
if hpg_yr:
    print("\nHPG (Non-Bank, CDKT) raw keys:")
    hpg_keys = sorted([k for k in hpg_yr[0].keys() if k.startswith("bsa")])
    print(f"Total bsa fields: {len(hpg_keys)}")
    non_nulls_hpg = {k: v for k, v in hpg_yr[0].items() if v is not None and k.startswith("bsa") and v != 0}
    print(f"Non-null/zero bsa fields: {len(non_nulls_hpg)}")
