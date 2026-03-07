"""
build_schema_mapper.py — Phase 6 CDKT/KQKD/LCTT Cross-Reference Mapper
=======================================================================
Mục đích: Tự động map tên dòng Excel Vietcap ↔ API key (bsa/isa/cfa)
          vào golden_schema.json để frontend hiển thị đầy đủ 87+ dòng.

Chiến lược:
  1. Load Excel BCTC của 1 ticker đại diện cho mỗi ngành.
  2. Fetch live API payload cho cùng ticker/period.
  3. Với mỗi dòng Excel (vị trí + tên VI), thử tìm API key bsa{N} có
     giá trị gần nhất với giá trị Excel ở cùng kỳ báo cáo.
  4. Nếu match confidence ≥ 0.99 (chênh lệch <1%), gán vietcap_key.
  5. Export report + cập nhật golden_schema.json.

Usage:
    python build_schema_mapper.py --sector bank    --ticker MBB  --sheet BS
    python build_schema_mapper.py --sector normal  --ticker FPT  --sheet BS
    python build_schema_mapper.py --sector sec     --ticker SSI  --sheet BS
    python build_schema_mapper.py --sector bank    --ticker MBB  --sheet IS
    python build_schema_mapper.py --sector bank    --ticker MBB  --sheet CF
    python build_schema_mapper.py --all  # Map tất cả sector × sheet

    # Dry-run: xem report mà không ghi vào schema
    python build_schema_mapper.py --sector bank --ticker MBB --sheet BS --dry-run
"""

import argparse
import json
import sys
import os
import math
import re
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).parent.parent.parent
V6_DIR  = Path(__file__).parent
V2_DIR  = ROOT / "sub-projects" / "V2_Data_Pipeline"
DATA_DIR = ROOT / "data" / "excel_imports"
SCHEMA_F = V2_DIR / "golden_schema.json"
REPORT_F = V6_DIR / "schema_mapping_report.md"

sys.path.insert(0, str(V2_DIR))

from dotenv import load_dotenv
load_dotenv(dotenv_path=ROOT / ".env", override=True)
os.environ['SUPABASE_KEY'] = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

import pandas as pd
import unicodedata
from sb_client import get_sb

# ── Config ────────────────────────────────────────────────────────────────

# Vietcap API key prefixes per sector × statement
API_PREFIX = {
    "BS": {"bank": "bsb", "sec": "bss", "normal": "bsa"},
    "IS": {"bank": "isb", "sec": "iss", "normal": "isa"},
    "CF": {"bank": "cfb", "sec": "cfs", "normal": "cfa"},
}

# Schema sheet IDs per sector × statement
SCHEMA_SHEET = {
    "BS": {"bank": "CDKT_BANK", "sec": "CDKT_SEC", "normal": "CDKT"},
    "IS": {"bank": "KQKD_BANK", "sec": "KQKD_SEC", "normal": "KQKD"},
    "CF": {"bank": "LCTT_BANK", "sec": "LCTT_SEC", "normal": "LCTT"},
}

# Excel sheet names per statement
EXCEL_SHEET = {
    "BS": "Balance Sheet",
    "IS": "Income Statement",
    "CF": "Cash Flow",
}

# Representative tickers for each sector (in priority order)
DEFAULT_TICKERS = {
    "bank":   ["MBB", "VCB", "TCB", "ACB"],
    "sec":    ["SSI", "VND"],
    "normal": ["FPT", "VHC", "VHM"],
}

# Row where period headers appear in Vietcap Excel (0-indexed)
HEADER_ROW = 10

# Match tolerance for value matching: allow 0.1% difference
MATCH_TOLERANCE = 0.001

# ── Helpers ───────────────────────────────────────────────────────────────

def remove_accents(input_str: str) -> str:
    """Remove Vietnamese accents and return lowercase string."""
    if not input_str:
        return ""
    # Normalize string to decomposed form
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    # Filter out combining characters
    only_ascii = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return only_ascii.replace('đ', 'd').replace('Đ', 'd').lower().strip()

def normalize_name(s: str) -> str:
    """Normalize Vietnamese string for fuzzy matching."""
    if not isinstance(s, str):
        return ""
    s = s.strip().lower()
    
    # Financial synonyms mapping
    s = s.replace("tổng cộng ", "tổng ")
    s = s.replace("tscđ", "tài sản cố định").replace("bđsđt", "bất động sản đầu tư")
    s = s.replace("tctd", "tổ chức tín dụng").replace("khác", "")
    s = s.replace("ctck", "công ty chứng khoán").replace("nhtm", "ngân hàng thương mại")
    s = s.replace("gdck", "giao dịch chứng khoán").replace("tndn", "thu nhập doanh nghiệp")
    s = s.replace("gtcl", "giá trị còn lại").replace("lnst", "lợi nhuận sau thuế")
    s = s.replace("(", "").replace(")", "").replace(",", "").replace(".", "")
    
    # Remove accents-aware → simple word comparison
    s = remove_accents(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

MANUAL_OVERRIDES = {
    # BANK - CDKT
    "cdkt_bank_tong_tai_san": "bsb96",
    "cdkt_bank_tong_no_phai_tra": "bsb126",
    "cdkt_bank_tong_von_chu_so_huu": "bsb131",
    "cdkt_bank_tong_cong_nguon_von": "bsb132",
    "cdkt_bank_loi_nhuan_sau_thue_thu_nhap_doanh_nghiep": "isb26",    
}


def values_match(v1, v2, tol=MATCH_TOLERANCE) -> bool:
    """Return True if two numeric values are within tolerance."""
    if v1 is None or v2 is None:
        return False
    try:
        f1, f2 = float(v1), float(v2)
        if not (math.isfinite(f1) and math.isfinite(f2)):
            return False
        if f1 == 0.0 and f2 == 0.0:
            return True
        if f1 == 0.0 or f2 == 0.0:
            return False  # One is zero, other isn't
        return abs(f1 - f2) / max(abs(f1), abs(f2)) <= tol
    except (TypeError, ValueError):
        return False


def load_excel_sheet(ticker: str, sheet: str) -> Optional[pd.DataFrame]:
    """Load one sheet from a Vietcap Excel BCTC file."""
    path = DATA_DIR / f"{ticker}_BCTC_Vietcap.xlsx"
    if not path.exists():
        print(f"  ❌ Excel not found: {path}")
        return None
    try:
        df = pd.read_excel(path, sheet_name=sheet, header=None, engine="openpyxl")
        print(f"  ✔ Loaded Excel {ticker}/{sheet}: {df.shape}")
        return df
    except Exception as e:
        print(f"  ❌ Excel read error: {e}")
        return None


def fetch_api_payload(ticker: str, statement: str) -> Optional[dict]:
    """Fetch live API payload for a given ticker and statement section."""
    from providers import VietcapProvider
    p = VietcapProvider()
    section_map = {
        "BS": "BALANCE_SHEET",
        "IS": "INCOME_STATEMENT",
        "CF": "CASH_FLOW",
    }
    section = section_map[statement]
    print(f"  🌐 Fetching API: {ticker} / {section} ...")
    payload = p.fetch_section(ticker, section)
    if not payload:
        print(f"  ❌ API returned None for {ticker}/{section}")
    else:
        print(f"  ✔ API: {len(payload.get('years',[]))}Y + {len(payload.get('quarters',[]))}Q periods")
    return payload


def find_period_columns(df: pd.DataFrame) -> dict:
    """Find column indices → period label from header row in Excel."""
    period_cols = {}
    header = df.iloc[HEADER_ROW]
    for col_idx, val in enumerate(header):
        if isinstance(val, str) and re.match(r'Q\d\s+\d{4}', val.strip()):
            p = val.strip()
            qnum = p[1]
            year = p[-4:]
            period_cols[col_idx] = f"Q{qnum}/{year}"
        elif isinstance(val, (int, float)) and 2010 <= val <= 2030:
            period_cols[col_idx] = str(int(val))
    return period_cols


def extract_excel_rows(df: pd.DataFrame) -> list[dict]:
    """Extract all data rows from Excel sheet after header."""
    rows = []
    period_cols = find_period_columns(df)
    for row_idx in range(HEADER_ROW + 1, len(df)):
        label = df.iloc[row_idx, 0]
        if not isinstance(label, str) or not label.strip():
            continue
        row_data = {
            "excel_row": row_idx,
            "label":     label.strip(),
            "label_norm": normalize_name(label),
            "values":    {},
        }
        for col_idx, period in period_cols.items():
            v = df.iloc[row_idx, col_idx]
            if isinstance(v, (int, float)) and math.isfinite(v):
                row_data["values"][period] = v
        rows.append(row_data)
    return rows


def build_api_value_lookup(payload: dict, prefix: str) -> dict:
    """
    Build lookup: {api_key: {period: value}} for all bsa/isa/cfa keys.
    Uses annual (years) data only for matching (more complete than quarters).
    """
    lookup = {}
    all_api_keys = set()
    for period_type in ("years", "quarters"):
        for api_row in payload.get(period_type, []):
            for k in api_row.keys():
                if k.startswith(prefix):
                    all_api_keys.add(k)

    for api_key in all_api_keys:
        lookup[api_key] = {}
        for period_type in ("years", "quarters"):
            for api_row in payload.get(period_type, []):
                yr = api_row.get("yearReport")
                lr = api_row.get("lengthReport")
                if period_type == "years" and yr:
                    period = str(int(yr))
                elif period_type == "quarters" and yr and lr in (1,2,3,4):
                    period = f"Q{int(lr)}/{int(yr)}"
                else:
                    continue
                lookup[api_key][period] = api_row.get(api_key)
    return lookup


def match_excel_to_api(excel_rows: list[dict], api_lookup: dict) -> list[dict]:
    """
    For each Excel row, find best-matching API key by value comparison.
    Returns enhanced rows with 'matched_key', 'confidence', 'match_count'.
    """
    results = []
    for row in excel_rows:
        best_key   = None
        best_score = 0
        best_count = 0

        if not row["values"]:
            results.append({**row, "matched_key": None, "confidence": 0.0, "match_count": 0})
            continue

        for api_key, api_periods in api_lookup.items():
            # Count matching periods
            match_n = 0
            total_n = 0
            for period, excel_val in row["values"].items():
                if period in api_periods:
                    total_n += 1
                    if values_match(excel_val, api_periods[period]):
                        match_n += 1

            if total_n == 0:
                continue
            score = match_n / total_n
            if score > best_score or (score == best_score and match_n > best_count):
                best_score = score
                best_key   = api_key
                best_count = match_n

        results.append({
            **row,
            "matched_key":  best_key,
            "confidence":   best_score,
            "match_count":  best_count,
        })
    return results


def match_schema_to_excel(schema_fields: list[dict], matched_excel: list[dict]) -> list[dict]:
    """
    Link schema fields to Excel matches by name similarity + value.
    Returns list of (field_id, vn_name, best_excel_match, api_key, confidence).
    """
    final = []
    used_excel_rows = set()

    for field in schema_fields:
        field_name_norm = normalize_name(field["vn_name"])
        best = None
        best_sim = 0.0

        for i, ex_row in enumerate(matched_excel):
            if i in used_excel_rows:
                continue
            if not ex_row.get("matched_key"):
                continue

            ex_name = ex_row["label_norm"]

            # Exact name match = highest priority
            if ex_name == field_name_norm:
                sim = 1.0
            elif field_name_norm in ex_name or ex_name in field_name_norm:
                sim = 0.85
            else:
                # Word overlap
                words_f = set(field_name_norm.split())
                words_e = set(ex_name.split())
                if words_f and words_e:
                    overlap = len(words_f & words_e)
                    sim = overlap / max(len(words_f), len(words_e))
                else:
                    sim = 0.0

            if sim > best_sim:
                best_sim = sim
                best = (i, ex_row)

        if best_sim >= 0.7 or (best and best_sim >= 0.4 and best[1].get("confidence", 0.0) >= 0.99):
            i, ex_row = best
            used_excel_rows.add(i)
            ex_conf = ex_row.get("confidence", 0.0)
            final.append({
                "field_id":       field["field_id"],
                "vn_name":        field["vn_name"],
                "schema_row":     field["row_number"],
                "excel_label":    ex_row["label"],
                "excel_row":      ex_row["excel_row"],
                "api_key":        ex_row.get("matched_key"),
                "name_sim":       round(best_sim, 2),
                "val_confidence": round(ex_conf, 2),
                "match_count":    ex_row.get("match_count", 0),
                "overall_conf":   round(best_sim * ex_conf, 2),
                "auto_map":       (best_sim >= 0.85 and ex_conf >= 0.80) or (best_sim >= 0.5 and ex_conf >= 0.99),
            })
        else:
            final.append({
                "field_id":   field["field_id"],
                "vn_name":    field["vn_name"],
                "schema_row": field["row_number"],
                "excel_label": None,
                "excel_row":   None,
                "api_key":     None,
                "name_sim":    0.0,
                "val_confidence": 0.0,
                "match_count": 0,
                "overall_conf": 0.0,
                "auto_map":     False,
            })
    return final


def update_schema(schema: dict, sector: str, statement: str,
                  matches: list[dict]) -> tuple[int, int]:
    """
    Write confirmed api_key mappings back into schema fields.
    Returns (updated_count, total_auto_mappable).
    """
    vietcap_key_sector = {
        "BS": {"bank": "bank", "sec": "sec", "normal": "normal"},
        "IS": {"bank": "bank", "sec": "sec", "normal": "normal"},
        "CF": {"bank": "bank", "sec": "sec", "normal": "normal"},
    }[statement]

    field_map = {f["field_id"]: f for f in schema["fields"]}
    updated = 0
    auto_map_total = sum(1 for m in matches if m["auto_map"] and m["api_key"])
    
    # Batch upsert to Supabase api_translation_dictionary
    supabase_dict = {}

    for match in matches:
        if not match["auto_map"] or not match["api_key"]:
            continue
        fid = match["field_id"]
        if fid not in field_map:
            continue
        field = field_map[fid]
        existing = field.get("vietcap_key") or {}
        if isinstance(existing, str):
            existing = {}  # Convert old-style to dict
        sector_key = vietcap_key_sector[sector]
        
        # Apply manual override if defined
        api_key_to_use = MANUAL_OVERRIDES.get(fid, match["api_key"])
        
        # Prepare for translation db
        vn_name_str = field["vn_name"]
        en_name_str = field.get("en_name", "")
        no_accents = remove_accents(vn_name_str)
        
        # Deduplicate using the composite unique key
        unique_key = f'{api_key_to_use}_{sector}_{statement}'
        supabase_dict[unique_key] = {
            "api_key": api_key_to_use,
            "sector": sector,
            "statement": statement,
            "vn_name": vn_name_str,
            "vn_name_no_accents": no_accents,
            "en_name": en_name_str
        }
        
        if existing.get(sector_key) == api_key_to_use:
            continue  # Already correct in JSON
            
        existing[sector_key] = api_key_to_use
        field["vietcap_key"] = existing
        updated += 1
        
    if supabase_dict:
        supabase_rows = list(supabase_dict.values())
        try:
            sb = get_sb()
            # Upsert into table (conflict on api_key, sector, statement)
            res = sb.table("api_translation_dictionary").upsert(
                supabase_rows, 
                on_conflict="api_key, sector, statement"
            ).execute()
            print(f"  ✅ Supabase: Upserted {len(supabase_rows)} translation records.")
        except Exception as e:
            print(f"  ❌ Supabase Upsert failed: {e}")

    return updated, auto_map_total


def write_report(sector: str, statement: str, ticker: str, matches: list[dict]):
    """Append a markdown section to the mapping report."""
    sheet_id = SCHEMA_SHEET[statement][sector]
    prefix   = API_PREFIX[statement][sector]

    auto_ok    = [m for m in matches if m["auto_map"] and m["api_key"]]
    auto_fail  = [m for m in matches if not m["auto_map"] or not m["api_key"]]
    total      = len(matches)

    with open(REPORT_F, "a", encoding="utf-8") as f:
        f.write(f"\n## {sheet_id} — {ticker} — {sector.upper()}\n")
        f.write(f"**Auto-mapped: {len(auto_ok)}/{total}** | "
                f"Needs review: {len(auto_fail)}\n\n")

        f.write("### ✅ Auto-mapped\n")
        f.write("| Schema Field | vn_name | Excel Label | API Key | Name Sim | Val Conf |\n")
        f.write("|---|---|---|---|---|---|\n")
        for m in auto_ok:
            f.write(f"| `{m['field_id']}` | {m['vn_name'][:40]} | "
                    f"{(m['excel_label'] or '')[:40]} | `{m['api_key']}` | "
                    f"{m['name_sim']} | {m['val_confidence']} |\n")

        if auto_fail:
            f.write("\n### ⚠️ Needs Manual Review\n")
            f.write("| Schema Field | vn_name | Best Excel | API Key | Name Sim | Val Conf |\n")
            f.write("|---|---|---|---|---|---|\n")
            for m in auto_fail[:40]:  # Limit to 40 rows
                f.write(f"| `{m['field_id']}` | {m['vn_name'][:40]} | "
                        f"{(m['excel_label'] or 'NO MATCH')[:40]} | "
                        f"`{m['api_key'] or 'NONE'}` | "
                        f"{m['name_sim']} | {m['val_confidence']} |\n")


# ── Main ──────────────────────────────────────────────────────────────────

def run_mapper(sector: str, statement: str, ticker: str, dry_run: bool = False):
    print(f"\n{'='*60}")
    print(f"  MAPPING: {sector.upper()} / {statement} / {ticker}")
    print(f"{'='*60}\n")

    schema_sheet_id = SCHEMA_SHEET[statement][sector]
    api_prefix      = API_PREFIX[statement][sector]
    excel_sheet_nm  = EXCEL_SHEET[statement]

    # 1. Load schema fields for this sector/statement combo
    with open(SCHEMA_F, encoding="utf-8") as f:
        schema = json.load(f)

    schema_fields = sorted(
        [fld for fld in schema["fields"] if fld["sheet"] == schema_sheet_id],
        key=lambda x: x["row_number"]
    )
    print(f"  Schema fields for {schema_sheet_id}: {len(schema_fields)}")

    # 2. Load Excel
    df_excel = load_excel_sheet(ticker, excel_sheet_nm)
    if df_excel is None:
        return 0, 0

    # 3. Fetch API
    payload = fetch_api_payload(ticker, statement)
    if not payload:
        return 0, 0

    # 4. Extract Excel rows + API lookup
    print("  📊 Extracting Excel rows & API values...")
    excel_rows  = extract_excel_rows(df_excel)
    api_lookup  = build_api_value_lookup(payload, api_prefix)
    print(f"  Excel rows: {len(excel_rows)} | API keys: {len(api_lookup)}")

    # 5. Match Excel rows → API keys by value
    print("  🔗 Matching Excel values → API keys...")
    matched_excel = match_excel_to_api(excel_rows, api_lookup)
    high_conf_xl = [m for m in matched_excel if m.get("confidence", 0) >= 0.8]
    print(f"  Excel rows with strong API match (≥80%): {len(high_conf_xl)}/{len(matched_excel)}")

    # 6. Match schema fields → Excel rows by name
    print("  🔗 Matching schema fields → Excel rows by name...")
    final_matches = match_schema_to_excel(schema_fields, matched_excel)
    auto_map_count = sum(1 for m in final_matches if m["auto_map"] and m["api_key"])
    print(f"  Auto-mappable: {auto_map_count}/{len(schema_fields)}")

    # 7. Write report
    write_report(sector, statement, ticker, final_matches)

    # 8. Update schema (unless dry-run)
    if not dry_run:
        updated, total_auto = update_schema(schema, sector, statement, final_matches)
        with open(SCHEMA_F, "w", encoding="utf-8") as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        print(f"  ✅ Schema updated: {updated}/{total_auto} keys written to golden_schema.json")
        return updated, total_auto
    else:
        print("  [DRY RUN] Schema NOT updated.")
        return 0, auto_map_count


def run_all(dry_run: bool):
    # Initialize report
    with open(REPORT_F, "w", encoding="utf-8") as f:
        f.write("# Schema Mapping Report — V6 CDKT/KQKD/LCTT Cross-Reference\n")
        f.write(f"> Generated: 2026-03-07\n\n")
        f.write("Mapping Excel Vietcap dòng tiếng Việt ↔ Vietcap API keys\n\n")

    total_updated = 0
    plan = [
        ("bank",   "BS", "MBB"),
        ("bank",   "IS", "MBB"),
        ("bank",   "CF", "MBB"),
        ("sec",    "BS", "SSI"),
        ("sec",    "IS", "SSI"),
        ("sec",    "CF", "SSI"),
        ("normal", "BS", "FPT"),
        ("normal", "IS", "FPT"),
        ("normal", "CF", "FPT"),
    ]

    for sector, stmt, ticker in plan:
        # Check Excel availability, try fallback
        xl_path = DATA_DIR / f"{ticker}_BCTC_Vietcap.xlsx"
        if not xl_path.exists():
            fallbacks = DEFAULT_TICKERS.get(sector, [])
            ticker = next((t for t in fallbacks
                           if (DATA_DIR / f"{t}_BCTC_Vietcap.xlsx").exists()), ticker)

        updated, total = run_mapper(sector, stmt, ticker, dry_run=dry_run)
        total_updated += updated

    print(f"\n{'='*60}")
    print(f"  ALL DONE. Total keys mapped: {total_updated}")
    print(f"  Report: {REPORT_F}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V6 Schema Mapper — Excel → API Key")
    parser.add_argument("--sector",    choices=["bank", "sec", "normal"], help="Sector")
    parser.add_argument("--ticker",    help="Ticker, e.g. MBB")
    parser.add_argument("--sheet",     choices=["BS", "IS", "CF"], help="Statement sheet")
    parser.add_argument("--dry-run",   action="store_true", help="Don't write to schema")
    parser.add_argument("--all",       action="store_true", help="Run all sectors × statements")
    args = parser.parse_args()

    if args.all:
        run_all(dry_run=args.dry_run)
    elif args.sector and args.sheet:
        ticker = args.ticker
        if not ticker:
            ticker = DEFAULT_TICKERS[args.sector][0]
        # Init report if single run
        if not REPORT_F.exists():
            with open(REPORT_F, "w", encoding="utf-8") as f:
                f.write("# Schema Mapping Report\n\n")
        run_mapper(args.sector, args.sheet, ticker, dry_run=args.dry_run)
    else:
        parser.print_help()
