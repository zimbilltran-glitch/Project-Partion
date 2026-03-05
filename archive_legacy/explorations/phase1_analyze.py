"""
V5 ImproData — Phase 1: Blueprint
P1.1 + P1.2 + P1.3: Analyze API key structure, compare with Supabase, audit golden_schema.json

Fetches raw API data for 3 representative tickers (FPT, MBB, SSI),
extracts all non-null keys, and compares against golden_schema.json mappings.
Outputs a comprehensive report to v5_phase1_report.json.
"""
import json, re, time, requests
from pathlib import Path
from collections import OrderedDict

BASE = Path(r'd:\Project_partial\Finsang\sub-projects\Version_2')
V5   = Path(r'd:\Project_partial\Finsang\sub-projects\V5_improdata')

API_URL = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/financial-statement?section={section}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://trading.vietcap.com.vn/",
    "Origin": "https://trading.vietcap.com.vn",
}

# Known Vietcap key prefixes per section
KNOWN_PREFIXES = {
    "BALANCE_SHEET":    ["bsa", "bsb", "bss", "bsi"],
    "INCOME_STATEMENT": ["isa", "isb", "iss", "isi"],
    "CASH_FLOW":        ["cfa", "cfb", "cfs", "cfi"],
    "NOTE":             ["noa", "nob", "nos", "noi"],
}

# Tickers representing each sector
TICKERS = {
    "FPT": "normal",   # Phi tài chính
    "MBB": "bank",     # Ngân hàng
    "SSI": "sec",      # Chứng khoán
}

SECTIONS = ["BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW"]


def fetch_api(ticker, section):
    """Fetch raw API data for a ticker/section combo."""
    url = API_URL.format(ticker=ticker, section=section)
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        data = r.json()
        if data.get("successful"):
            return data.get("data", {})
    except Exception as e:
        return {"error": str(e)}
    return None


def extract_keys(api_row):
    """Extract all non-null financial keys from one API period row.
    Returns dict: {key: value} sorted by extracted numeric index."""
    pattern = re.compile(r'^(bsa|bsb|bss|bsi|isa|isb|iss|isi|cfa|cfb|cfs|cfi|noa|nob|nos|noi)(\d+)$')
    keys = {}
    for k, v in api_row.items():
        m = pattern.match(k)
        if m and v is not None:
            keys[k] = v
    return keys


def sort_api_keys(keys_dict):
    """Sort API keys by prefix group then by numeric index."""
    pattern = re.compile(r'^([a-z]+)(\d+)$')
    def key_sort(k):
        m = pattern.match(k)
        if m:
            return (m.group(1), int(m.group(2)))
        return (k, 0)
    return OrderedDict(sorted(keys_dict.items(), key=lambda x: key_sort(x[0])))


def load_schema():
    """Load golden_schema.json and return fields grouped by sheet."""
    with open(BASE / "golden_schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    sheets = {}
    for field in schema.get("fields", []):
        sheet = field.get("sheet", "UNKNOWN")
        if sheet not in sheets:
            sheets[sheet] = []
        sheets[sheet].append(field)
    
    # Sort by row_number within each sheet
    for sheet in sheets:
        sheets[sheet].sort(key=lambda x: x.get("row_number", 0))
    
    return sheets


def audit_schema_keys(schema_sheets):
    """Audit golden_schema.json for empty vietcap_key values."""
    report = {}
    for sheet, fields in schema_sheets.items():
        total = len(fields)
        has_key = sum(1 for f in fields if f.get("vietcap_key"))
        empty = total - has_key
        report[sheet] = {
            "total_fields": total,
            "has_vietcap_key": has_key,
            "empty_vietcap_key": empty,
            "coverage_pct": round(has_key / total * 100, 1) if total > 0 else 0,
            "empty_field_ids": [f["field_id"] for f in fields if not f.get("vietcap_key")]
        }
    return report


def main():
    results = {
        "generated_at": "2026-03-04",
        "purpose": "V5 Phase 1 — API Key Structure Analysis & Schema Audit",
        "api_key_analysis": {},
        "schema_audit": {},
        "comparison": {},
    }
    
    # ─── P1.1: Fetch & Analyze API key structure ──────────────────────
    for ticker, sector in TICKERS.items():
        results["api_key_analysis"][ticker] = {"sector": sector, "sections": {}}
        
        for section in SECTIONS:
            data = fetch_api(ticker, section)
            if not data or "error" in (data if isinstance(data, dict) else {}):
                results["api_key_analysis"][ticker]["sections"][section] = {
                    "status": "FAILED",
                    "error": str(data)
                }
                continue
            
            # Save raw data
            raw_dir = V5 / "_raw"
            raw_dir.mkdir(exist_ok=True)
            with open(raw_dir / f"{ticker}_{section}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Extract keys from latest year row
            years = data.get("years", [])
            if not years:
                results["api_key_analysis"][ticker]["sections"][section] = {
                    "status": "NO_DATA", "years_count": 0
                }
                continue
            
            latest_year = years[0]
            all_keys = extract_keys(latest_year)
            sorted_keys = sort_api_keys(all_keys)
            
            # Group by prefix
            prefix_groups = {}
            for k in sorted_keys:
                m = re.match(r'^([a-z]+)(\d+)$', k)
                if m:
                    prefix = m.group(1)
                    if prefix not in prefix_groups:
                        prefix_groups[prefix] = []
                    prefix_groups[prefix].append(k)
            
            results["api_key_analysis"][ticker]["sections"][section] = {
                "status": "OK",
                "year": latest_year.get("yearReport"),
                "total_non_null_keys": len(sorted_keys),
                "prefix_groups": {p: {"count": len(keys), "range": f"{keys[0]}..{keys[-1]}"} 
                                  for p, keys in prefix_groups.items()},
                "all_keys_sample": list(sorted_keys.keys())[:20],
            }
            
            time.sleep(0.5)  # Rate limit courtesy
        
        time.sleep(1)  # Between tickers
    
    # ─── P1.3: Audit golden_schema.json ───────────────────────────────
    schema_sheets = load_schema()
    results["schema_audit"] = audit_schema_keys(schema_sheets)
    
    # ─── P1.2: Comparison summary ─────────────────────────────────────
    # Compare FPT API keys vs CDKT schema fields
    fpt_bs = results["api_key_analysis"].get("FPT", {}).get("sections", {}).get("BALANCE_SHEET", {})
    cdkt_audit = results["schema_audit"].get("CDKT", {})
    
    results["comparison"] = {
        "balance_sheet": {
            "api_keys_count": fpt_bs.get("total_non_null_keys", 0),
            "schema_fields_count": cdkt_audit.get("total_fields", 0),
            "schema_mapped_count": cdkt_audit.get("has_vietcap_key", 0),
            "schema_unmapped_count": cdkt_audit.get("empty_vietcap_key", 0),
            "verdict": "CRITICAL_GAP" if cdkt_audit.get("empty_vietcap_key", 0) > 0 else "OK",
        }
    }
    
    # ─── Write report ─────────────────────────────────────────────────
    report_path = V5 / "v5_phase1_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
