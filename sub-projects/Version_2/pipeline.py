"""
Phase A/T — Architect + Trigger: Core Pipeline
pipeline.py — Vietcap API → Normalize → Parquet (Hive) → GC → Supabase log

API field key convention (confirmed Phase L + Phase A refinement):
  The integer N in keys like bsa{N}, isa{N}, cfa{N}, noa{N} is NOT the absolute
  Excel row number — it is the 1-indexed sequential position within that sheet's
  field list (i.e., the position among all rows in that section/tab).

  Balance Sheet  : bsa{N}, bsb{N}, bss{N}, bsi{N}   (N = 1..~287)
  Income Stmt    : isa{N}, isb{N}, iss{N}, isi{N}   (N = 1..~180)
  Cash Flow      : cfa{N}, cfb{N}, cfs{N}, cfi{N}   (N = 1..~80)
  Note           : noa{N}, nos{N}, noi{N}            (N = 1..~413)

  Example: isa5  → 5th row of Income Statement  = Lợi nhuận gộp
           bsa96 → 96th row of Balance Sheet    = TỔNG CỘNG TÀI SẢN + NV

Phase T (Trigger):
  Supabase `pipeline_runs` logging enabled via .env (SUPABASE_URL + SUPABASE_KEY).
  Each section run logs one row. Graceful fallback if supabase-py not installed.

Usage:
  python Version_2/pipeline.py --ticker VHC
  python Version_2/pipeline.py --ticker FPT
  python Version_2/run_all.py          # runs all FINSANG_TICKERS from .env
"""

import argparse, json, re, os
from pathlib import Path
from datetime import datetime

# ── Phase T: load .env credentials gracefully ─────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # python-dotenv not installed; secrets from OS environment

import pandas as pd
from providers import BaseProvider, VietcapProvider
import pyarrow as pa
import pyarrow.parquet as pq
import io
from security import get_cipher

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent.parent
SCHEMA_F   = Path(__file__).parent / "golden_schema.json"
DATA_DIR   = ROOT / "data" / "financial"
TMP_DIR    = ROOT / ".tmp" / "raw"
LOG_FILE   = Path(__file__).parent / "pipeline.log"

# ─── API Providers ──────────────────────────────────────────────────────────────

SECTION_MAP = {
    "BALANCE_SHEET":    "CDKT",
    "INCOME_STATEMENT": "KQKD",
    "CASH_FLOW":        "LCTT",
    "NOTE":             "NOTE",
}

# Phase 2: Sector routing via centralized sector.py (replaces hardcoded lists)
from sector import get_sheets_for_ticker, get_sector

# When processing, we need to know which section a sheet maps TO (e.g. CDKT_BANK -> BALANCE_SHEET)
SHEET_TO_SECTION = {
    "CDKT": "BALANCE_SHEET",
    "KQKD": "INCOME_STATEMENT",
    "LCTT": "CASH_FLOW",
    "NOTE": "NOTE",
    "CDKT_BANK": "BALANCE_SHEET",
    "KQKD_BANK": "INCOME_STATEMENT",
    "LCTT_BANK": "CASH_FLOW",
    "CDKT_SEC": "BALANCE_SHEET",
    "KQKD_SEC": "INCOME_STATEMENT",
    "LCTT_SEC": "CASH_FLOW"
}

# ─── Load Golden Schema ───────────────────────────────────────────────────────
def load_schema() -> dict[str, list[dict]]:
    """Returns {sheet_id → sorted list of field dicts} from golden_schema.json"""
    with open(SCHEMA_F, encoding="utf-8") as f:
        raw = json.load(f)
    schema = {}
    for field in raw["fields"]:
        sid = field["sheet"]
        schema.setdefault(sid, []).append(field)
    for sid in schema:
        schema[sid].sort(key=lambda x: x["row_number"])
    return schema

# fetch_section is now handled by the Provider class.

# ─── Save raw JSON to .tmp/ ───────────────────────────────────────────────────
def save_raw(ticker: str, section: str, payload: dict) -> Path:
    tmp_dir = TMP_DIR / ticker.upper()
    tmp_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = tmp_dir / f"{section.lower()}_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return out

# API_PREFIX and get_api_value are now handled by the Provider class.

# ─── Normalize: build flat DataFrame from API payload ─────────────────────────
def normalize(payload: dict, section: str, sheet_id: str,
              schema_fields: list[dict], provider: BaseProvider) -> pd.DataFrame:
    """
    Convert one API section payload into a tidy long-format DataFrame.

    Column schema:
        ticker | period_type | period_label | sheet | field_id
        vn_name | value | unit | level | sheet_row_idx | vietcap_mapped

    Key design decision (Phase A refinement):
        schema_fields must be sorted by row_number (load_schema() guarantees this).
        We use enumerate(..., start=1) to get the 1-indexed position within the sheet,
        which exactly matches the Vietcap API key integer (e.g. isa5 = 5th IS field).

    Quarter period encoding:
        yearReport   = calendar year (e.g. 2024)
        lengthReport = 1|2|3|4 for quarterly, 5 for full-year annual rows
    """
    records = []

    for period_type in ("years", "quarters"):
        rows = payload.get(period_type, [])
        for api_row in rows:
            yr = api_row.get("yearReport")
            lr = api_row.get("lengthReport")   # 1-4 = quarter, 5 = full year

            if period_type == "quarters":
                # Quarter: lengthReport = 1|2|3|4
                q_num = int(lr) if lr and int(lr) in (1, 2, 3, 4) else None
                period_label = f"Q{q_num}/{int(yr)}" if (q_num and yr) else (
                               f"Q?/{int(yr)}" if yr else "unknown")
                pt_tag = "quarter"
            else:
                period_label = str(int(yr)) if yr else "unknown"
                pt_tag = "year"

            ticker = api_row.get("ticker", api_row.get("organCode", "?"))

            for idx, field in enumerate(schema_fields, start=1):
                field_id = field.get("field_id", "")
                
                
                vietcap_key = field.get("vietcap_key")
                if vietcap_key:
                    val = provider.get_api_value_by_key(api_row, vietcap_key)
                else:
                    vietcap_idx = idx
                    val = provider.get_api_value(api_row, section, vietcap_idx, field_id)
                    
                records.append({
                    "ticker":         ticker,
                    "period_type":    pt_tag,
                    "period_label":   period_label,
                    "sheet":          sheet_id,
                    "field_id":       field["field_id"],
                    "vn_name":        field["vn_name"],
                    "value":          val,
                    "unit":           field["unit"],
                    "level":          field["level"],
                    "sheet_row_idx":  field.get("row_number"),  # stored for debug/audit
                    "vietcap_mapped": val is not None,
                })

    return pd.DataFrame(records)

# ─── Write Parquet with Hive partitioning ─────────────────────────────────────
def write_parquet(df: pd.DataFrame, ticker: str, period_type: str, sheet_id: str):
    out_dir = DATA_DIR / ticker.upper() / f"period_type={period_type}" / f"sheet={sheet_id.lower()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{ticker.upper()}.parquet"
    table = pa.Table.from_pandas(df, preserve_index=False)
    
    cipher = get_cipher()
    if cipher:
        buf = io.BytesIO()
        pq.write_table(table, buf, compression="snappy")
        encrypted_data = cipher.encrypt(buf.getvalue())
        with open(out_file, "wb") as f:
            f.write(encrypted_data)
    else:
        pq.write_table(table, out_file, compression="snappy")
    
    return out_file

# ─── Garbage Collection: delete .tmp/ after successful Parquet write ──────────
def cleanup_tmp(ticker: str):
    tmp_dir = TMP_DIR / ticker.upper()
    if tmp_dir.exists():
        for f in tmp_dir.iterdir():
            f.unlink()
        print(f"  GC: cleaned .tmp/raw/{ticker.upper()}/")

# ─── Log to pipeline.log ──────────────────────────────────────────────────────
def log_run(ticker: str, section: str, sheet_id: str,
            n_periods: int, status: str, note: str = ""):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
    line = f"{ts} | {ticker} | Phase-T | pipeline.py | {sheet_id} | {n_periods} periods | {status} | {note}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(f"  Logged: {line}")

# ─── Phase T: Supabase pipeline_runs INSERT ──────────────────────────────────
def log_supabase(ticker: str, sheet_id: str, period_type: str,
                 n_periods: int, n_fields: int, mapped_pct: float,
                 parquet_path: str, status: str, error_log: str = "") -> bool:
    """
    Insert one row into Supabase `pipeline_runs` table.
    Gracefully skips if:
      - supabase-py not installed
      - SUPABASE_URL / SUPABASE_KEY missing from environment
      - Network error

    Returns: True if successfully inserted, False otherwise.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print(f"  Supabase: SUPABASE_URL/KEY not set - skipping cloud log")
        return False

    try:
        from supabase import create_client
    except ImportError:
        print(f"  Supabase: supabase-py not installed - pip install supabase")
        return False

    try:
        sb = create_client(url, key)
        payload = {
            "ticker":            ticker.upper(),
            "sheet":             sheet_id.upper(),
            "period_type":       period_type,
            "n_periods":         n_periods,
            "n_fields":          n_fields,
            "mapped_pct":        round(mapped_pct, 2),
            "source":            "vietcap",
            "extraction_method": "api",
            "status":            status,
            "error_log":         error_log or None,
            "parquet_path":      parquet_path,
            "phase":             "T",
        }
        sb.table("pipeline_runs").insert(payload).execute()
        print(f"  Supabase: logged {ticker}/{sheet_id} ({status})")
        return True
    except Exception as e:
        print(f"  Supabase insert failed (non-fatal): {e}")
        return False


# ─── Main pipeline ────────────────────────────────────────────────────────────
def run_pipeline(ticker: str, provider: BaseProvider = None):
    provider = provider or VietcapProvider()
    schema = load_schema()
    print(f"\n{'='*60}")
    print(f"  FINSANG PIPELINE v2.0 - {ticker.upper()}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    parquet_ok = []

    target_sheets = get_sheets_for_ticker(ticker.upper())

    for section, sheet_id in target_sheets:
        print(f"  RUN: {section} ({sheet_id})")
        sheet_fields = schema.get(sheet_id, [])
        if not sheet_fields:
            print(f"    No fields in Golden Schema for {sheet_id} - skipping")
            continue

        # 1. Fetch via Provider
        payload = provider.fetch_section(ticker, section)
        if not payload:
            log_run(ticker, section, sheet_id, 0, "FAIL", "API fetch returned None")
            continue

        # 2. Save raw to .tmp/
        raw_path = save_raw(ticker, section, payload)
        n_years    = len(payload.get("years", []))
        n_quarters = len(payload.get("quarters", []))
        print(f"    Fetched: {n_years}Y + {n_quarters}Q periods")

        # 3. Normalize
        df = normalize(payload, section, sheet_id, sheet_fields, provider)
        mapped_pct = df["vietcap_mapped"].mean() * 100
        print(f"    Normalized: {len(df)} rows | Mapped: {mapped_pct:.1f}%")

        # 4. Write Parquet per period_type
        last_pq_path = ""
        for pt in df["period_type"].unique():
            sub = df[df["period_type"] == pt].copy()
            pq_path = write_parquet(sub, ticker, pt, sheet_id)
            last_pq_path = str(pq_path.relative_to(ROOT))
            print(f"    Parquet: {last_pq_path}")
            parquet_ok.append((section, sheet_id, pt))

        n_periods = n_years + n_quarters
        n_fields  = len(sheet_fields)
        log_run(ticker, section, sheet_id, n_periods, "SUCCESS",
                f"Normalized {len(df)} rows, mapped {mapped_pct:.1f}%")

        # 5. Phase T: log to Supabase pipeline_runs (non-fatal)
        log_supabase(
            ticker=ticker,
            sheet_id=sheet_id,
            period_type="both",
            n_periods=n_periods,
            n_fields=n_fields,
            mapped_pct=mapped_pct,
            parquet_path=last_pq_path,
            status="success",
        )


    # 5. Garbage collection (only if all sections succeeded)
    sections_ok = len(set(s[0] for s in parquet_ok))
    if sections_ok == len(SECTION_MAP):
        cleanup_tmp(ticker)
    else:
        failed = len(SECTION_MAP) - sections_ok
        print(f"\n  {failed} section(s) failed - .tmp/ retained for debugging")

    print(f"\n{'='*60}")
    print(f"  Pipeline complete: {sections_ok}/{len(SECTION_MAP)} sections OK")
    print(f"{'='*60}\n")


# ─── Tab loader utility ───────────────────────────────────────────────────────
SHEET_TO_TABLE = {
    "cdkt":       "balance_sheet",
    "cdkt_bank":  "balance_sheet",
    "cdkt_sec":   "balance_sheet",
    "kqkd":       "income_statement",
    "kqkd_bank":  "income_statement",
    "kqkd_sec":   "income_statement",
    "lctt":       "cash_flow",
    "lctt_bank":  "cash_flow",
    "lctt_sec":   "cash_flow",
    "cstc":       "financial_ratios",
}

def load_tab_from_supabase(ticker: str, period_type: str, sheet: str) -> pd.DataFrame:
    """
    Load filtered data from Supabase for UI tab switching.
    Pivots long-format Supabase rows into the wide format expected by UI.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY not found in environment.")

    try:
        from supabase import create_client
    except ImportError:
        raise ImportError("supabase-py not installed. Run 'pip install supabase'.")

    sb = create_client(url, key)
    table_name = SHEET_TO_TABLE.get(sheet.lower())
    if not table_name:
        raise ValueError(f"Invalid sheet: {sheet}")

    print(f"[{ticker}] Fetching {period_type} {table_name} from Supabase...")
    try:
        data = []
        page_size = 1000
        for page in range(10):  # max 10k rows
            start = page * page_size
            end = start + page_size - 1
            response = sb.table(table_name).select("*").eq("stock_name", ticker).range(start, end).execute()
            data.extend(response.data)
            if len(response.data) < page_size:
                break
    except Exception as e:
        print(f"Supabase fetch failed (non-fatal): {e}")
        data = [] # Assign empty list on error to allow pd.DataFrame([])
    
    df_long = pd.DataFrame(data)
    
    # Filter by period pattern (V2 convention: "2024" or "Q1/2024")
    if period_type == "year":
        df_long = df_long[df_long["period"].str.match(r"^\d{4}$")]
    elif period_type == "quarter":
        df_long = df_long[df_long["period"].str.match(r"^Q\d/\d{4}$")]

    if df_long.empty:
        return pd.DataFrame()

    # Load Golden Schema to ensure order
    schema_f = Path(__file__).parent / "golden_schema.json"
    schema_raw = json.loads(schema_f.read_text(encoding="utf-8"))
    ordered_fields = [f for f in schema_raw["fields"] if f["sheet"].upper() == sheet.upper()]

    def sort_p(p):
        if str(p).startswith("Q"):
            try: return (int(p[3:]), int(p[1]))
            except: pass
        try: return (int(p), 0)
        except: return (0, 0)

    all_periods = sorted(df_long["period"].unique(), key=sort_p, reverse=True)
    
    rows = []
    # financial_ratios table has 'ratio_name' instead of 'item'
    item_col = "ratio_name" if table_name == "financial_ratios" else "item"
    id_col = "id" if table_name == "financial_ratios" else "item_id"

    # For standard statements with golden schema match, use schema order
    # For sector-specific sheets (cdkt_bank, etc.), use row_number order from Supabase
    if table_name != "financial_ratios" and ordered_fields:
        for field in ordered_fields:
            fid = field["field_id"]
            sub = df_long[df_long["item_id"] == fid]
            if sub.empty: continue
            
            row_dict = {
                "field_id": fid,
                "vn_name":  field["vn_name"],
                "unit":     field["unit"],
                "level":    field["level"],
            }
            for p in all_periods:
                p_row = sub[sub["period"] == p]
                row_dict[p] = p_row["value"].values[0] if not p_row.empty else None
            rows.append(row_dict)
    elif table_name != "financial_ratios":
        # Sector-specific sheets: no golden schema match, use row_number order
        unique_items = df_long.drop_duplicates(subset=["item_id"]).sort_values("row_number")
        for _, item_row in unique_items.iterrows():
            fid = item_row["item_id"]
            sub = df_long[df_long["item_id"] == fid]
            row_dict = {
                "field_id": fid,
                "vn_name":  item_row.get("item", fid),
                "unit":     item_row.get("unit", "tỷ đồng"),
                "level":    int(item_row.get("levels", 0)),
            }
            for p in all_periods:
                p_row = sub[sub["period"] == p]
                row_dict[p] = p_row["value"].values[0] if not p_row.empty else None
            rows.append(row_dict)
    else:
        # For ratios, just group by ratio_name
        for ratio in df_long[item_col].unique():
            sub = df_long[df_long[item_col] == ratio]
            row_dict = {
                "field_id": ratio,
                "vn_name":  ratio,
                "unit":     "%",
                "level":    0,
            }
            for p in all_periods:
                p_row = sub[sub["period"] == p]
                row_dict[p] = p_row["value"].values[0] if not p_row.empty else None
            rows.append(row_dict)

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)
    # Ensure columns are in order: metadata then periods (desc)
    meta_cols = ["field_id", "vn_name", "unit", "level"]
    period_cols = [c for c in result.columns if c not in meta_cols]
    return result[meta_cols + sorted(period_cols, key=sort_p, reverse=True)]

def load_tab(ticker: str, period_type: str, sheet: str) -> pd.DataFrame:
    """
    Load filtered Parquet for UI tab switching.
    Args:
        ticker:      e.g. 'VHC'
        period_type: 'year' | 'quarter'
        sheet:       'cdkt' | 'kqkd' | 'lctt' | 'note'
    Returns: DataFrame with columns: field_id, vn_name, unit, level, + one col per period_label
             Rows sorted by original Golden Schema row_number order (top → bottom of statement)
    """
    pq_path = (DATA_DIR / ticker.upper()
               / f"period_type={period_type}"
               / f"sheet={sheet.lower()}"
               / f"{ticker.upper()}.parquet")
    if not pq_path.exists():
        raise FileNotFoundError(f"No Parquet found at {pq_path}. Run pipeline first.")

    cipher = get_cipher()
    if cipher:
        with open(pq_path, "rb") as f:
            encrypted_data = f.read()
        try:
            decrypted_data = cipher.decrypt(encrypted_data)
            df = pd.read_parquet(io.BytesIO(decrypted_data))
        except Exception:
            # Fallback if file is actually not encrypted
            df = pd.read_parquet(pq_path)
    else:
        df = pd.read_parquet(pq_path)

    # Sort periods newest → oldest
    all_periods = sorted(df["period_label"].unique(), reverse=True)

    # Build wide form while preserving field order from Golden Schema
    # Group by field_id, preserving insertion order (which matches row_number order)
    schema_f = Path(__file__).parent / "golden_schema.json"
    import json as _json
    schema_raw = _json.loads(schema_f.read_text(encoding="utf-8"))
    ordered_fields = [
        f for f in schema_raw["fields"]
        if f["sheet"].upper() == sheet.upper()
    ]

    rows = []
    for field in ordered_fields:
        fid = field["field_id"]
        sub = df[df["field_id"] == fid]
        if sub.empty:
            continue
        row_dict = {
            "field_id": fid,
            "vn_name":  field["vn_name"],
            "unit":     field["unit"],
            "level":    field["level"],
        }
        for p in all_periods:
            p_row = sub[sub["period_label"] == p]
            row_dict[p] = p_row["value"].values[0] if not p_row.empty else None
        rows.append(row_dict)

    result = pd.DataFrame(rows)
    period_cols = [c for c in result.columns if c not in ("field_id", "vn_name", "unit", "level")]
    return result[["field_id", "vn_name", "unit", "level"] + sorted(period_cols, reverse=True)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Finsang V2.0 Pipeline")
    parser.add_argument("--ticker", required=True, help="Stock ticker, e.g. VHC")
    args = parser.parse_args()
    run_pipeline(args.ticker)
