"""
T2.1 — Probe Vietcap API cho SEC prefix (iss, bss, cfs)
Mục tiêu:
  1. Fetch raw API response cho 3 CTCK đại diện: SSI, VCI, VND
  2. Liệt kê toàn bộ keys trả về (iss*, bss*, cfs*) kèm tên + giá trị mẫu
  3. So sánh với golden_schema.json SEC fields → phát hiện mismatch
  4. Xuất báo cáo _sec_mapping_audit.txt
"""
import requests
import json
import sys
from pathlib import Path

ROOT     = Path(__file__).parent.parent.parent
SEC_RAW  = Path(__file__).parent / "_raw_sec"
SEC_RAW.mkdir(exist_ok=True)
AUDIT_OUT = Path(__file__).parent / "_sec_mapping_audit.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Referer": "https://trading.vietcap.com.vn/",
    "Origin": "https://trading.vietcap.com.vn",
}

SEC_TICKERS = ["SSI", "VCI", "VND"]
SECTIONS    = ["BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW"]

# --- Fetch raw API -------------------------------------------------------
def fetch_section(ticker: str, section: str) -> dict:
    url = (
        f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/"
        f"company/{ticker}/financial-statement?section={section}"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  [WARN] {ticker} {section}: {e}")
        return {}

# --- Extract all non-null keys from API response -------------------------
def extract_keys(payload: dict) -> dict:
    """
    Returns {key: {"name": ..., "sample_val": ...}} for all non-null iss/bss/cfs keys.
    Looks at years[0] (most recent annual data).
    """
    key_map = {}
    rows = payload.get("years", []) or payload.get("quarters", [])
    if not rows:
        return key_map
    sample_row = rows[0]
    for k, v in sample_row.items():
        if v is not None and isinstance(v, (int, float, str)):
            # Only track financial data keys (iss, bss, cfs, isa, bsa, cfa...)
            if any(k.startswith(p) for p in ("iss", "bss", "cfs", "isa", "bsa", "cfa", "isb", "bsb", "cfb")):
                key_map[k] = {"sample_val": v}
    # Try to get names from the items array if available
    for item in payload.get("items", []):
        key = item.get("key") or item.get("field")
        name = item.get("name") or item.get("label") or ""
        if key and key in key_map:
            key_map[key]["name"] = name
    return key_map

# --- Load golden schema SEC fields --------------------------------------
def load_sec_schema() -> dict:
    """Returns {sheet: [{field_id, vn_name, vietcap_key}, ...]} for SEC sheets."""
    schema_path = ROOT / "sub-projects" / "Version_2" / "golden_schema.json"
    with open(schema_path, encoding="utf-8") as f:
        raw = json.load(f)
    sec = {}
    for field in raw["fields"]:
        sheet = field.get("sheet", "")
        if "SEC" in sheet or sheet in ("CDKT_SEC", "KQKD_SEC", "LCTT_SEC"):
            sec.setdefault(sheet, []).append({
                "field_id":    field.get("field_id", ""),
                "vn_name":     field.get("vn_name", ""),
                "vietcap_key": field.get("vietcap_key"),
                "vietcap_mapped": field.get("vietcap_mapped", False),
            })
    return sec

# --- Main audit ---------------------------------------------------------
def main():
    lines = []
    lines.append("=" * 70)
    lines.append("T2.1 — SEC API Mapping Audit Report")
    lines.append("Tickers: " + ", ".join(SEC_TICKERS))
    lines.append("=" * 70)

    # 1. Fetch & save raw API for SSI, VCI, VND
    all_sec_keys = {}  # ticker → section → key_map
    for ticker in SEC_TICKERS:
        all_sec_keys[ticker] = {}
        for section in SECTIONS:
            print(f"Fetching {ticker} {section}...")
            payload = fetch_section(ticker, section)
            if payload:
                # Save raw
                raw_file = SEC_RAW / f"{ticker}_{section.lower()}.json"
                with open(raw_file, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False)
                # Extract keys
                key_map = extract_keys(payload)
                all_sec_keys[ticker][section] = key_map
                print(f"  -> {len(key_map)} non-null keys found")
            else:
                all_sec_keys[ticker][section] = {}

    # 2. Cross-reference: what keys do SEC tickers actually use?
    lines.append("\n" + "=" * 70)
    lines.append("SECTION A — Keys actually returned by API per Section")
    lines.append("=" * 70)

    section_key_union = {}  # section → set of keys across all 3 tickers
    for ticker in SEC_TICKERS:
        for section, key_map in all_sec_keys[ticker].items():
            if section not in section_key_union:
                section_key_union[section] = {}
            for k, v in key_map.items():
                if k not in section_key_union[section]:
                    section_key_union[section][k] = {"tickers": [], "sample": v.get("sample_val")}
                section_key_union[section][k]["tickers"].append(ticker)

    for section, key_map in sorted(section_key_union.items()):
        lines.append(f"\n  [{section}]  — {len(key_map)} unique keys across {SEC_TICKERS}")
        # Group by key prefix
        by_prefix = {}
        for k in sorted(key_map.keys()):
            prefix = "".join(c for c in k if not c.isdigit())
            by_prefix.setdefault(prefix, []).append(k)
        for prefix, keys in sorted(by_prefix.items()):
            lines.append(f"    Prefix '{prefix}': {len(keys)} keys  [{keys[0]} .. {keys[-1]}]")

    # 3. Load golden schema and cross-reference
    lines.append("\n" + "=" * 70)
    lines.append("SECTION B — Golden Schema SEC fields vs API keys")
    lines.append("=" * 70)

    sec_schema = load_sec_schema()
    for sheet, fields in sorted(sec_schema.items()):
        n_mapped    = sum(1 for f in fields if f["vietcap_mapped"])
        n_with_key  = sum(1 for f in fields if f["vietcap_key"])
        lines.append(f"\n  [{sheet}]  {len(fields)} fields | "
                     f"mapped={n_mapped} | has_vietcap_key={n_with_key}")

        # Find which prefix these fields use
        prefix_counts = {}
        for f in fields:
            vk = f["vietcap_key"]
            if isinstance(vk, dict):
                key = vk.get("sec", "")
            elif isinstance(vk, str):
                key = vk
            else:
                key = ""
            if key:
                prefix = "".join(c for c in key if not c.isdigit())
                prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
        if prefix_counts:
            lines.append(f"    Schema key prefixes: {dict(prefix_counts)}")

    # 4. Key summary: identify SEC-specific prefixes confirmed
    lines.append("\n" + "=" * 70)
    lines.append("SECTION C — Confirmed SEC Key Prefixes")
    lines.append("=" * 70)

    for section, key_map in sorted(section_key_union.items()):
        prefixes = set()
        for k in key_map:
            prefix = "".join(c for c in k if not c.isdigit())
            prefixes.add(prefix)
        # Separate shared (isa/bsa) from SEC-specific (iss/bss/cfs)
        shared = {p for p in prefixes if p in ("isa", "bsa", "cfa")}
        sec_only = prefixes - shared
        lines.append(f"\n  {section}:")
        lines.append(f"    Shared keys (same as normal): {sorted(shared)}")
        lines.append(f"    SEC-specific keys           : {sorted(sec_only)}")

    # 5. Write audit file
    audit_text = "\n".join(lines)
    with open(AUDIT_OUT, "w", encoding="utf-8") as f:
        f.write(audit_text)

    print(f"\nAudit saved: {AUDIT_OUT}")
    print(audit_text)

if __name__ == "__main__":
    main()
