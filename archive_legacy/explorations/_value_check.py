"""
V5 Phase 2 FIX — Value-based key matching instead of sequential.

Core insight: The Vietcap API bsa keys are NOT in 1:1 sequential order 
with our schema. Key bsa96 = "Tổng cộng tài sản" but it's at position 66 
in our schema. We need VALUE-based matching.

Strategy:
1. For each schema field, find the API key that contains the matching value
2. Use FPT 2024 annual data as reference
3. For ambiguous values (0, null), use the closest positional neighbor
4. Cross-validate with the Vietcap website
"""
import json, re
from pathlib import Path
from collections import OrderedDict

V2   = Path(r'd:\Project_partial\Finsang\sub-projects\Version_2')
V5   = Path(r'd:\Project_partial\Finsang\sub-projects\V5_improdata')

# ─── Load schema ──────────────────────────────────────────────────────────────
with open(V2 / "golden_schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

# ─── Load raw API data for cross-reference ────────────────────────────────────
def load_raw_years(ticker, section):
    with open(V5 / "_raw" / f"{ticker}_{section}.json", "r", encoding="utf-8") as f:
        return json.load(f)

def extract_all_prefix_keys_sorted(api_data, prefix):
    """Get all keys for prefix from ALL years, sorted by numeric index."""
    pattern = re.compile(rf'^{prefix}(\d+)$')
    all_keys = set()
    for yr in api_data.get("years", []):
        for k, v in yr.items():
            m = pattern.match(k)
            if m and v is not None:
                all_keys.add(k)
    return sorted(all_keys, key=lambda x: int(re.match(rf'{prefix}(\d+)', x).group(1)))

def get_year_data(api_data, year=2024, length=5):
    """Get a specific year's data."""
    for yr in api_data.get("years", []):
        if yr.get("yearReport") == year and yr.get("lengthReport") == length:
            return yr
    # Fallback to most recent
    years = api_data.get("years", [])
    return max(years, key=lambda x: x.get("yearReport", 0)) if years else {}

# ─── Value-based matching approach ────────────────────────────────────────────
# For FPT 2024, fetch the data that SHOULD be on Vietcap web.
# Then match each displayed value to an API key.

# However, we don't have web-scraped labels. So we use a HYBRID approach:
# 1. Sequential mapping gives us the APPROXIMATE mapping
# 2. We validate by checking known anchor values
# 3. Where mismatches found, we correct by value-searching

# Actually, the simplest correct approach:
# The current sequential mapping assigns key[i] to field[i].
# This IS correct INTERNALLY (the values we store are consistent with the API).
# The issue is that our ANCHOR POINTS (bsa96=Total Assets) were hardcoded 
# based on an INCORRECT assumption that key numbers equal row positions.
# 
# In reality:
# - The sequential mapping bsa1→field[0], bsa2→field[1], ..., bsa66→field[65]  
#   IS correct because the API returns these values in THIS order for normal companies.
# - The old hardcoded mapping (bsa96=Total Assets) was wrong because it assumed
#   key number 96 = row 96, when actually Total Assets is at key position 66.
#
# VERIFICATION: Let's check if bsa66 value in API matches what Vietcap shows 
# as "Tổng cộng tài sản" on the web.

fpt_bs = load_raw_years("FPT", "BALANCE_SHEET")
yr2024 = get_year_data(fpt_bs, 2024, 5)

log = []
log.append("=" * 70)
log.append("VALUE VERIFICATION: Sequential mapping vs known fields")
log.append("=" * 70)

# Get ALL bsa keys sorted
all_bsa = extract_all_prefix_keys_sorted(fpt_bs, "bsa")
log.append(f"Total bsa keys: {len(all_bsa)}")
log.append(f"First 10: {all_bsa[:10]}")
log.append(f"Keys 60-70: {all_bsa[60:70] if len(all_bsa) > 70 else 'N/A'}")

# Check specific keys
key_checks = {
    "bsa1": "TÀI SẢN NGẮN HẠN",
    "bsa53": "??? at position 53",
    "bsa66": "field[65] in our schema = cdkt_tong_cong_tai_san?",
    "bsa96": "Real Tổng cộng tài sản (old hardcoded)",
}

for key, label in key_checks.items():
    val = yr2024.get(key)
    log.append(f"  {key:10s} = {val:>25} | Expected: {label}")

# Now the REAL check: 
# What value does the Vietcap WEB show for "Tổng cộng tài sản" for FPT 2024?
# From the earlier raw probe, bsa96 = 71999995678620.0
# But our sequential mapping maps cdkt_tong_cong_tai_san to bsa66 = 1835037318363.0
# 
# 71,999 tỷ makes sense for FPT total assets
# 1,835 tỷ does NOT (too small for a 72,000 tỷ company)
#
# This PROVES sequential mapping is WRONG for some fields.
# The keys are NOT in simple 1:1 correspondence.

log.append("\n" + "=" * 70)
log.append("CONCLUSION: Sequential mapping FAILS")
log.append("Need to use BROWSER SCRAPING to get ground truth labels.")
log.append("=" * 70)

# Let's try another approach: TOTAL KEY ENUMERATION with value matching
# Use multiple years to find unique value patterns
log.append("\n" + "=" * 70)
log.append("APPROACH 2: Multi-year value fingerprinting")
log.append("=" * 70)

# Build fingerprint for each bsa key: tuple of values across years
years_data = [get_year_data(fpt_bs, y, 5) for y in range(2018, 2025)]
years_data = [y for y in years_data if y]

# For cdkt_tong_cong_tai_san, we know bsa96 should be ~72 tỷ for 2024
# Let's find which sequential position bsa96 falls at
for pos, key in enumerate(all_bsa):
    if key == "bsa96":
        log.append(f"  bsa96 is at sequential position {pos} (0-indexed)")
        break

# Check: our schema expects cdkt_tong_cong_tai_san at field index 65
# But bsa96 is at position 95 (0-indexed) in the sorted key list
# This means there are 96 bsa keys before bsa96, but our schema has
# cdkt_tong_cong_tai_san at position 65 (only 66 fields into the schema)

# The truth: Vietcap's schema has MORE rows than our simplified schema
# Our 122-field CDKT schema is a SUBSET of Vietcap's ~123 bsa keys
# But they're in DIFFERENT ORDER or have different items

# Let me check the actual key numbers in detail:
log.append(f"\nAll bsa key numbers: {[int(re.match(r'bsa(\d+)', k).group(1)) for k in all_bsa]}")

# Check if keys 1-96 are all present (sequential block for Assets + Liabilities + Equity)
key_nums = [int(re.match(r'bsa(\d+)', k).group(1)) for k in all_bsa]
sequential_part = [n for n in key_nums if n <= 96]
gaps_in_96 = [i for i in range(1, 97) if i not in sequential_part]
log.append(f"\nKeys 1-96: {len(sequential_part)} present, gaps: {gaps_in_96}")

after_96 = [n for n in key_nums if n > 96]
log.append(f"Keys >96: {after_96}")

# If keys 1-96 are fully sequential (no gaps), then:
# - bsa1..bsa96 = the main 96 items (TÀI SẢN + NỢ + VỐN + TỔNG)
# - bsa159+ = supplementary items  
# - Our schema has 122 fields, which = 96 + 26 supplementary
# This means the FIRST 96 fields in our schema should map to bsa1..bsa96
# And field[96]..field[121] should map to bsa159, bsa160, etc.

# Let's verify: field[65] should NOT be cdkt_tong_cong_tai_san
# because bsa66 != "Tổng cộng tài sản"

with open(V5 / "_value_analysis.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log))
