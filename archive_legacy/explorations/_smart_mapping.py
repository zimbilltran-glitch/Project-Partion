"""
V5 Phase 2 FIX — Smart mapping using value fingerprinting + known anchor points.

The problem: Sequential mapping (bsa[i] → field[i]) is wrong because 
Vietcap's schema order differs from our golden_schema.json order.

Solution: Use VALUE MATCHING across multiple years.
For each schema field, find the API key whose multi-year value fingerprint 
matches uniquely. For ambiguous cases (all zeros), use nearest-neighbor.
"""
import json, re
from pathlib import Path

V2 = Path(r'd:\Project_partial\Finsang\sub-projects\Version_2')
V5 = Path(r'd:\Project_partial\Finsang\sub-projects\V5_improdata')

with open(V2 / "golden_schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

# ─── Load Bank schema anchors (GROUND TRUTH) ─────────────────────────────────
# Bank schema already has correct keys. Extract the pattern to understand
# Vietcap's logical ordering.
bank_fields = [f for f in schema["fields"] if f["sheet"] == "CDKT_BANK"]
bank_fields.sort(key=lambda x: x.get("row_number", 0))

# Bank field row 1 = "TỔNG TÀI SẢN" → bsa53
# This tells us bsa53 is the "Total Assets" for ALL company types!
bank_anchors = {f["vn_name"].strip().upper(): f["vietcap_key"] for f in bank_fields}

# ─── Build GROUND TRUTH anchors from Bank schema ─────────────────────────────
# Map VN names to known correct keys
known_mapping = {}
for bf in bank_fields:
    name = bf["vn_name"].strip()
    key = bf["vietcap_key"]
    # If the key uses bsa prefix, it's shared with normal companies
    if key.startswith("bsa"):
        known_mapping[name.upper()] = key

log = []
log.append("=" * 70)
log.append("GROUND TRUTH from Bank schema (bsa keys only):")
log.append("=" * 70)
for name, key in sorted(known_mapping.items(), key=lambda x: x[1]):
    log.append(f"  {key:12s} = {name}")

# ─── Load raw API data ───────────────────────────────────────────────────────
with open(V5 / "_raw" / "FPT_BALANCE_SHEET.json", "r", encoding="utf-8") as f:
    fpt_bs = json.load(f)

# Get multiple years for fingerprinting
years_data = []
for yr in fpt_bs.get("years", []):
    if yr.get("lengthReport") == 5:  # Annual only
        years_data.append(yr)
years_data.sort(key=lambda x: x.get("yearReport", 0))

# Build fingerprint: key → [val_2018, val_2019, ..., val_2024]
bsa_pattern = re.compile(r'^bsa(\d+)$')
all_bsa_keys = set()
for yr in years_data:
    for k in yr:
        if bsa_pattern.match(k):
            all_bsa_keys.add(k)
all_bsa_sorted = sorted(all_bsa_keys, key=lambda x: int(bsa_pattern.match(x).group(1)))

key_fingerprints = {}
for key in all_bsa_sorted:
    vals = []
    for yr in years_data:
        v = yr.get(key)
        vals.append(v if v is not None else 0)
    key_fingerprints[key] = tuple(vals)

# ─── Now map CDKT fields using value matching ─────────────────────────────────
cdkt_fields = [f for f in schema["fields"] if f["sheet"] == "CDKT"]
cdkt_fields.sort(key=lambda x: x.get("row_number", 0))

# Strategy 1: Use Bank schema name-based matching for shared field names
log.append(f"\n{'='*70}")
log.append("MAPPING STRATEGY: Name matching from Bank anchors + value matching")
log.append("=" * 70)

# Current (wrong) sequential mapping gives us field[i] → bsa_sorted[i]
# The correct mapping requires matching field names to API keys

# Bank schema gives us these bsa anchors:
# TỔNG TÀI SẢN → bsa53
# Tiền mặt, vàng bạc, đá quý → bsa2
# Góp vốn, đầu tư dài hạn → bsa43
# Tài sản cố định → bsa29
# etc.

# For NORMAL company, the field names are DIFFERENT from bank names
# So we can't directly reuse bank names.

# Strategy 2: Field-level value matching
# Read the OLD Supabase data for FPT to get the "currently displayed" values
# Then match those values to API keys

# Wait - the OLD Supabase data used the WRONG mapping, so those values are wrong.
# We need a different anchor.

# Strategy 3: The GOLD approach
# The Vietcap website displayss data using bsa53 as total assets.
# bsa53 = bsa96 = 71999995678620.0 for 2024 (they're the SAME value!)
# Let me check if MORE keys share values

# Check for duplicate values
yr_2024 = None
for yr in years_data:
    if yr.get("yearReport") == 2024:
        yr_2024 = yr
        break

value_to_keys = {}
for key in all_bsa_sorted:
    val = yr_2024.get(key) if yr_2024 else None
    if val is not None:
        val_key = float(val)
        if val_key not in value_to_keys:
            value_to_keys[val_key] = []
        value_to_keys[val_key].append(key)

duplicates = {v: ks for v, ks in value_to_keys.items() if len(ks) > 1}
log.append(f"\nDuplicate values in 2024 data: {len(duplicates)}")
for val, ks in sorted(duplicates.items(), key=lambda x: -abs(x[0]))[:20]:
    log.append(f"  {val:>25,.0f} → {ks}")

# Key insight from duplicates:
# bsa53 and bsa96 share the SAME value (71,999 tỷ = Total Assets)
# This suggests bsa96 is a COPY/REFERENCE of bsa53
# The real "Tổng cộng tài sản" in Vietcap's ordering is bsa53

# Strategy 4: ROW-COUNTING approach
# Vietcap's BS has exactly 96 rows (bsa1-bsa96) for the main statement
# Our schema has 96 fields BEFORE the gap (fields 0-95), then 26 supplementary
# Wait, let me check: how many fields are before cdkt_tong_cong_tai_san?

for i, f in enumerate(cdkt_fields):
    if f["field_id"] == "cdkt_tong_cong_tai_san":
        log.append(f"\ncdkt_tong_cong_tai_san is at field index {i} (0-based), row_number {f['row_number']}")
        break
    if f["field_id"] == "cdkt_tong_cong_nguon_von":
        log.append(f"cdkt_tong_cong_nguon_von is at field index {i}")

# The issue: Our schema has 66 fields before TỔNG TÀI SẢN (0-indexed 65)
# But Vietcap puts it at position 53 (0-indexed 52)
# So our schema has 13 MORE sub-items than Vietcap in the Assets section

# The root: Our schema follows TT200 standard (Vietnamese accounting)
# while Vietcap uses a SIMPLIFIED/DIFFERENT breakdown

# FINAL SOLUTION: We need to match BY NAME, not by position.
# Cross-reference our VN names with the Vietcap web display order.

# Since we can't scrape the web easily, let's use the BANK schema as reference.
# The Bank schema has field names like "Tài sản cố định" → bsa29
# Normal CDKT also has "Tài sản cố định" → should also be bsa29!

name_to_api_key = {}  # Build from Bank schema
for bf in bank_fields:
    name = bf["vn_name"].strip()
    key = bf["vietcap_key"]
    if key.startswith("bsa"):
        name_to_api_key[name] = key

log.append(f"\n{'='*70}")
log.append(f"Name-based matches from Bank schema ({len(name_to_api_key)} bsa keys):")

matched = 0
unmatched = []
for i, f in enumerate(cdkt_fields):
    vn_name = f["vn_name"].strip()
    if vn_name in name_to_api_key:
        old_key = f["vietcap_key"]
        new_key = name_to_api_key[vn_name]
        if old_key != new_key:
            log.append(f"  FIX [{i:3d}] {vn_name:45s}: {old_key:10s} → {new_key}")
        matched += 1
    else:
        unmatched.append((i, vn_name, f["vietcap_key"]))

log.append(f"\n  Matched: {matched}/{len(cdkt_fields)}")
log.append(f"  Unmatched: {len(unmatched)}")
for idx, name, key in unmatched[:30]:
    log.append(f"    [{idx:3d}] {name:50s} (current: {key})")

with open(V5 / "_smart_mapping_analysis.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log))
