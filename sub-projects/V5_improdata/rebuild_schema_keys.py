"""
V5 Phase 2 — P2.2: Rebuild golden_schema.json with correct vietcap_key values.

Strategy (proven by analysis):
- For CDKT/KQKD/LCTT (normal company), the bsa/isa/cfa keys ARE sequential
  and map 1:1 to schema fields sorted by row_number.
- For NOTE, use noa keys (same sequential pattern).
- Bank/SEC sheets are already 100% mapped — DO NOT TOUCH.
"""
import json, re
from pathlib import Path
from collections import OrderedDict

BASE = Path(r'd:\Project_partial\Finsang\sub-projects\Version_2')
V5   = Path(r'd:\Project_partial\Finsang\sub-projects\V5_improdata')

# ─── Load data ────────────────────────────────────────────────────────────────
with open(BASE / "golden_schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

def load_raw(ticker, section):
    with open(V5 / "_raw" / f"{ticker}_{section}.json", "r", encoding="utf-8") as f:
        return json.load(f)

def extract_prefix_keys(api_data, prefix):
    """Extract keys with given prefix, return sorted list of key strings."""
    pattern = re.compile(rf'^{prefix}(\d+)$')
    years = api_data.get("years", [])
    if not years:
        return []
    
    # Use ALL years to find all possible keys (some keys null in certain years)
    all_keys = set()
    for yr in years:
        for k, v in yr.items():
            m = pattern.match(k)
            if m and v is not None:
                all_keys.add(k)
    
    # Sort by numeric suffix
    return sorted(all_keys, key=lambda x: int(re.match(rf'{prefix}(\d+)', x).group(1)))

# ─── Mapping config ──────────────────────────────────────────────────────────
# Sheet → (API section, key prefix, reference ticker)
SHEET_CONFIG = {
    "CDKT": ("BALANCE_SHEET", "bsa", "FPT"),
    "KQKD": ("INCOME_STATEMENT", "isa", "FPT"),
    "LCTT": ("CASH_FLOW", "cfa", "FPT"),
    "NOTE": ("NOTE", "noa", "FPT"),
}

# Sheets to SKIP (already 100% mapped)
SKIP_SHEETS = {"CDKT_BANK", "KQKD_BANK", "LCTT_BANK", "CDKT_SEC", "KQKD_SEC", "LCTT_SEC"}

# ─── Build mapping ───────────────────────────────────────────────────────────
log = []
updated_count = 0

for sheet, (section, prefix, ticker) in SHEET_CONFIG.items():
    # Get schema fields for this sheet
    fields = [f for f in schema["fields"] if f["sheet"] == sheet]
    fields.sort(key=lambda x: x.get("row_number", 0))
    
    if not fields:
        log.append(f"[SKIP] {sheet}: no fields found in schema")
        continue
    
    # Load raw API data and extract keys
    try:
        raw = load_raw(ticker, section)
    except FileNotFoundError:
        # NOTE section might not have raw data — try fetching
        log.append(f"[SKIP] {sheet}: no raw data file for {ticker}_{section}")
        continue
    
    api_keys = extract_prefix_keys(raw, prefix)
    
    log.append(f"\n{'='*60}")
    log.append(f"[{sheet}] Schema fields: {len(fields)} | API {prefix} keys: {len(api_keys)}")
    
    if len(api_keys) < len(fields):
        log.append(f"  ⚠️  WARNING: fewer API keys than schema fields ({len(api_keys)} < {len(fields)})")
        log.append(f"  → Will map what we can, remaining fields get empty key")
    
    # Sequential mapping
    for i, field in enumerate(fields):
        old_key = field.get("vietcap_key", "")
        if i < len(api_keys):
            new_key = api_keys[i]
        else:
            new_key = ""
            log.append(f"  ⚠️  field[{i}] '{field['field_id']}' has no matching API key")
        
        # Update in the original schema
        field["vietcap_key"] = new_key
        if new_key:
            field["vietcap_mapped"] = True
        
        if old_key != new_key:
            updated_count += 1
            if i < 5 or new_key == "":  # Log first 5 and unmapped
                log.append(f"  field[{i}] '{field['field_id']}': '{old_key}' → '{new_key}'")
    
    log.append(f"  ✅ Mapped {min(len(fields), len(api_keys))}/{len(fields)} fields")

# Handle NOTE separately — try with noa prefix from FPT BS response
# NOTE data comes from BALANCE_SHEET section in Vietcap API (it's embedded)
note_fields = [f for f in schema["fields"] if f["sheet"] == "NOTE"]
note_fields.sort(key=lambda x: x.get("row_number", 0))
if note_fields:
    raw_bs = load_raw("FPT", "BALANCE_SHEET")
    # Try noa prefix first, then nob
    noa_keys = extract_prefix_keys(raw_bs, "noa")
    nob_keys = extract_prefix_keys(raw_bs, "nob")
    
    # Also check NOTE section raw data if it exists
    try:
        raw_note = load_raw("FPT", "NOTE")  
        noa_keys_note = extract_prefix_keys(raw_note, "noa")
        nob_keys_note = extract_prefix_keys(raw_note, "nob")
        if len(noa_keys_note) > len(noa_keys):
            noa_keys = noa_keys_note
        if len(nob_keys_note) > len(nob_keys):
            nob_keys = nob_keys_note
    except FileNotFoundError:
        pass
    
    # Combine noa + nob keys as the full NOTE key set
    all_note_keys = noa_keys + nob_keys
    
    log.append(f"\n{'='*60}")
    log.append(f"[NOTE] Schema fields: {len(note_fields)} | noa keys: {len(noa_keys)} | nob keys: {len(nob_keys)} | total: {len(all_note_keys)}")
    
    for i, field in enumerate(note_fields):
        old_key = field.get("vietcap_key", "")
        if i < len(all_note_keys):
            new_key = all_note_keys[i]
        else:
            new_key = ""
        
        field["vietcap_key"] = new_key
        if new_key:
            field["vietcap_mapped"] = True
        
        if old_key != new_key:
            updated_count += 1
    
    log.append(f"  ✅ Mapped {min(len(note_fields), len(all_note_keys))}/{len(note_fields)} fields")

# ─── Save updated schema ─────────────────────────────────────────────────────
output_path = BASE / "golden_schema.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)

log.append(f"\n{'='*60}")
log.append(f"TOTAL updated fields: {updated_count}")
log.append(f"Saved to: {output_path}")

# ─── Post-rebuild audit ──────────────────────────────────────────────────────
audit = {}
for field in schema["fields"]:
    sheet = field.get("sheet", "UNKNOWN")
    if sheet not in audit:
        audit[sheet] = {"total": 0, "mapped": 0, "empty": 0}
    audit[sheet]["total"] += 1
    if field.get("vietcap_key"):
        audit[sheet]["mapped"] += 1
    else:
        audit[sheet]["empty"] += 1

log.append(f"\n{'='*60}")
log.append("POST-REBUILD AUDIT:")
for sheet, counts in sorted(audit.items()):
    pct = round(counts["mapped"] / counts["total"] * 100, 1) if counts["total"] else 0
    status = "✅" if counts["empty"] == 0 else "⚠️"
    log.append(f"  {status} {sheet:12s}: {counts['mapped']}/{counts['total']} mapped ({pct}%), {counts['empty']} empty")

# Write log
with open(V5 / "_rebuild_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log))
