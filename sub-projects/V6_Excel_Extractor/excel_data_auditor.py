"""
V6 Excel Data Auditor - Phase 6.2 + 6.3
========================================
Phase 6.2  → Extract NPL/CASA from Excel → Upsert to Supabase (source='V6_EXCEL')
Phase 6.3  → Ground Truth Validator: Compare V6_EXCEL vs CFO_CALC_V2, overwrite 0.0 values

Structure verified from MBB_BCTC_Vietcap.xlsx (2026-03-07):
  Balance Sheet:
    Row 10  → Period headers  (2018..2025 annual, Q1 2018..Q4 2025 quarterly)
    Row 22  → Cho vay khách hàng (NPL denominator)
  Note Sheet:
    Row 10  → Same period headers
    Row 78  → Nợ dưới tiêu chuẩn     (NPL Group 3)
    Row 79  → Nợ nghi ngờ             (NPL Group 4)
    Row 80  → Nợ xấu có khả năng mất vốn (NPL Group 5)
    Row 130 → Tổng tiền gửi KH        (CASA denominator)
    Row 131 → Tiền gửi không kỳ hạn   (CASA numerator)

Period format standard: Q4/2024 (4-digit year) — aligned with balance_sheet table.
"""

import pandas as pd
import json
import os
import sys
import concurrent.futures
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "sub-projects" / "V2_Data_Pipeline"))

# Load env for Supabase
load_dotenv(dotenv_path=ROOT / "frontend" / ".env")
URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
KEY = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
os.environ["SUPABASE_URL"] = URL
os.environ["SUPABASE_KEY"] = KEY

from sb_client import get_sb
sb = get_sb()
from sector import get_sector

# ─────────────────────────────────────────────
# CONSTANTS: Row indices (0-based, header=None)
# Verified from MBB_BCTC_Vietcap.xlsx
# ─────────────────────────────────────────────
HEADER_ROW          = 10   # Period names (shared between BS and Note)
BS_TOTAL_LOANS_ROW  = 22   # Cho vay khách hàng (gross)
NOTE_NPL3_ROW       = 78   # Nợ dưới tiêu chuẩn
NOTE_NPL4_ROW       = 79   # Nợ nghi ngờ
NOTE_NPL5_ROW       = 80   # Nợ xấu có khả năng mất vốn
NOTE_TOTAL_DEP_ROW  = 130  # Tổng tiền gửi phân theo loại
NOTE_CASA_ROW       = 131  # Tiền gửi không kỳ hạn

# Tolerance for Ground Truth comparison (absolute % difference)
GT_TOLERANCE        = 0.01  # 0.01% difference threshold
EXCEL_READ_TIMEOUT  = 90   # seconds — kill read_excel if it hangs


def read_excel_with_timeout(filepath: str, timeout: int = EXCEL_READ_TIMEOUT, **kwargs) -> pd.DataFrame:
    """
    Safe wrapper for pd.read_excel() with a hard timeout.
    Raises TimeoutError if the file takes longer than `timeout` seconds.
    Prevents process hanging on large/corrupt Excel files (CTO Audit finding 2026-03-07).
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(pd.read_excel, filepath, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(
                f"read_excel() on '{filepath}' exceeded {timeout}s timeout. "
                "File may be corrupted or too large."
            )


def map_excel_period(p_str: str) -> str | None:
    """
    Convert Excel period string to DB standard format.
    'Q4 2024' → 'Q4/2024'  (4-digit year, standard)
    Annual years (e.g. 2024) → skip (return None)
    """
    p = str(p_str).strip()
    if p.startswith("Q"):
        parts = p.split(" ")          # ['Q4', '2024']
        if len(parts) == 2:
            return f"{parts[0]}/{parts[1]}"   # Q4/2024 (full year)
    return None   # Annual year → skip


def build_period_col_map(df: pd.DataFrame) -> dict:
    """
    Read header row (ROW 10) → build {col_index: period_db_string} for quarterly periods.
    """
    header = df.iloc[HEADER_ROW]
    period_map = {}
    for col_idx, val in enumerate(header):
        if pd.notna(val):
            mapped = map_excel_period(str(val))
            if mapped:
                period_map[col_idx] = mapped
    return period_map


def safe_float(val) -> float | None:
    try:
        v = float(val)
        return v if pd.notna(val) else None
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════════════════
# PHASE 6.2 — PARSER: Extract NPL & CASA from Excel
# ═══════════════════════════════════════════════════════

def verify_excel_layout(ticker: str, df_bs: pd.DataFrame, df_note: pd.DataFrame) -> bool:
    """
    Sanity-check: verify that expected row indices contain the correct keywords.
    If Vietcap changes their Excel layout, this will FAIL LOUD instead of
    silently returning wrong numbers. (CTO Audit recommendation 2026-03-07)
    """
    errors = []

    # Check Balance Sheet row LOANS
    bs_label = str(df_bs.iloc[BS_TOTAL_LOANS_ROW, 0]).lower()
    if "cho vay" not in bs_label:
        errors.append(f"BS Row {BS_TOTAL_LOANS_ROW}: expected 'cho vay', got '{bs_label[:40]}'")

    # Check Note NPL rows
    npl3_label = str(df_note.iloc[NOTE_NPL3_ROW, 0]).lower()
    if "nợ" not in npl3_label and "no" not in npl3_label:
        errors.append(f"Note Row {NOTE_NPL3_ROW}: expected NPL keyword, got '{npl3_label[:40]}'")

    # Check Note CASA row
    casa_label = str(df_note.iloc[NOTE_CASA_ROW, 0]).lower()
    if "không kỳ hạn" not in casa_label and "khong ky han" not in casa_label:
        errors.append(f"Note Row {NOTE_CASA_ROW}: expected 'không kỳ hạn', got '{casa_label[:40]}'")

    if errors:
        print(f"  ⚠️  [{ticker}] LAYOUT VERIFICATION FAILED — Vietcap may have changed Excel structure:")
        for e in errors:
            print(f"      ❌ {e}")
        return False

    print(f"  ✔ [{ticker}] Layout verification passed.")
    return True


def parse_bank_NPL_CASA(ticker: str, df_bs: pd.DataFrame, df_note: pd.DataFrame) -> list[dict]:
    """
    Extract NPL ratio and CASA ratio for all quarterly periods from Excel.
    Returns list of ratio dicts ready for Supabase upsert.
    """
    print(f"[{ticker}] Building period map from Note sheet...")
    period_map = build_period_col_map(df_note)
    print(f"[{ticker}] Found {len(period_map)} quarterly periods: {list(period_map.values())[:5]}...")

    # ── Extract raw rows ──────────────────────────────────
    total_loans_row  = df_bs.iloc[BS_TOTAL_LOANS_ROW]
    npl3_row         = df_note.iloc[NOTE_NPL3_ROW]
    npl4_row         = df_note.iloc[NOTE_NPL4_ROW]
    npl5_row         = df_note.iloc[NOTE_NPL5_ROW]
    total_dep_row    = df_note.iloc[NOTE_TOTAL_DEP_ROW]
    casa_row         = df_note.iloc[NOTE_CASA_ROW]

    # Sanity check labels
    print(f"  ✔ [BS]   Row {BS_TOTAL_LOANS_ROW}: '{df_bs.iloc[BS_TOTAL_LOANS_ROW, 0]}'")
    print(f"  ✔ [Note] Row {NOTE_NPL3_ROW}: '{df_note.iloc[NOTE_NPL3_ROW, 0]}'")
    print(f"  ✔ [Note] Row {NOTE_NPL4_ROW}: '{df_note.iloc[NOTE_NPL4_ROW, 0]}'")
    print(f"  ✔ [Note] Row {NOTE_NPL5_ROW}: '{df_note.iloc[NOTE_NPL5_ROW, 0]}'")
    print(f"  ✔ [Note] Row {NOTE_TOTAL_DEP_ROW}: '{df_note.iloc[NOTE_TOTAL_DEP_ROW, 0]}'")
    print(f"  ✔ [Note] Row {NOTE_CASA_ROW}: '{df_note.iloc[NOTE_CASA_ROW, 0]}'")

    ratios = []

    for col_idx, period_db in period_map.items():
        # ── NPL ratio ──────────────────────────────────────
        total_loans = safe_float(total_loans_row.iloc[col_idx])
        n3 = safe_float(npl3_row.iloc[col_idx]) or 0.0
        n4 = safe_float(npl4_row.iloc[col_idx]) or 0.0
        n5 = safe_float(npl5_row.iloc[col_idx]) or 0.0

        if total_loans and total_loans > 0:
            npl_ratio = round(((n3 + n4 + n5) / total_loans) * 100, 4)
            ratios.append({
                "stock_name": ticker,
                "asset_type": "STOCK",
                "ratio_name": "Tỷ lệ nợ xấu (%)",
                "period": period_db,
                "value": npl_ratio,
                "source": "V6_EXCEL",
                "item_id": "bank_4_10",
                "levels": 1,
                "row_number": 71,
                "unit": "%"
            })

        # ── CASA ratio ─────────────────────────────────────
        total_dep = safe_float(total_dep_row.iloc[col_idx])
        casa_val  = safe_float(casa_row.iloc[col_idx])

        if total_dep and total_dep > 0 and casa_val is not None:
            casa_ratio = round((casa_val / total_dep) * 100, 4)
            ratios.append({
                "stock_name": ticker,
                "asset_type": "STOCK",
                "ratio_name": "Tỷ lệ CASA",
                "period": period_db,
                "value": casa_ratio,
                "source": "V6_EXCEL",
                "item_id": "bank_4_7",
                "levels": 1,
                "row_number": 68,
                "unit": "%"
            })

    return ratios


# ═══════════════════════════════════════════════════════
# PHASE 6.3 — GROUND TRUTH VALIDATOR
# Compare V6_EXCEL (Ground Truth) vs CFO_CALC_V2 (API)
# Overwrite API rows that have wrong values (0.0 or significant drift)
# ═══════════════════════════════════════════════════════

def run_ground_truth_validator(ticker: str, dry_run: bool = False) -> dict:
    """
    Compare V6_EXCEL (Excel Ground Truth) vs CFO_CALC_V2 (API-computed) values.
    Overwrites API records where:
      - API value is 0.0 but Excel has real data, OR
      - Difference exceeds GT_TOLERANCE (absolute %)

    Returns summary dict with counts of matches/fixes.
    """
    print(f"\n{'─'*50}")
    print(f"[Phase 6.3] Ground Truth Validator for {ticker}")
    print(f"{'─'*50}")

    RATIO_NAMES = ["Tỷ lệ nợ xấu (%)", "Tỷ lệ CASA"]

    # ── Pull Excel Ground Truth from DB ──────────────────
    excel_res = sb.table("financial_ratios")\
        .select("ratio_name,period,value")\
        .eq("stock_name", ticker)\
        .eq("source", "V6_EXCEL")\
        .in_("ratio_name", RATIO_NAMES)\
        .execute()

    if not excel_res.data:
        print(f"⚠️  No V6_EXCEL data found for {ticker}. Run extraction phase first.")
        return {"ticker": ticker, "status": "no_excel_data"}

    # Build lookup: (ratio_name, period) → excel_value
    excel_lookup: dict[tuple, float] = {}
    for row in excel_res.data:
        key = (row["ratio_name"], row["period"])
        excel_lookup[key] = float(row["value"])

    print(f"[{ticker}] V6_EXCEL records loaded: {len(excel_lookup)}")

    # ── Pull API (CFO_CALC_V2) records ───────────────────
    api_res = sb.table("financial_ratios")\
        .select("id,ratio_name,period,value")\
        .eq("stock_name", ticker)\
        .eq("source", "CFO_CALC_V2")\
        .in_("ratio_name", RATIO_NAMES)\
        .execute()

    if not api_res.data:
        print(f"⚠️  No CFO_CALC_V2 data found for {ticker}.")
        return {"ticker": ticker, "status": "no_api_data"}

    print(f"[{ticker}] CFO_CALC_V2 records loaded: {len(api_res.data)}")

    # ── Compare & collect fixes ───────────────────────────
    stats = {"matched": 0, "fixed": 0, "missing_in_excel": 0, "skipped": 0}
    fixes = []

    for api_row in api_res.data:
        ratio_name = api_row["ratio_name"]
        period     = api_row["period"]
        api_val    = float(api_row["value"]) if api_row["value"] is not None else None
        row_id     = api_row["id"]

        excel_val = excel_lookup.get((ratio_name, period))

        if excel_val is None:
            stats["missing_in_excel"] += 1
            continue

        # API value is 0.0 but Excel has real data → definitely wrong
        api_is_zero  = (api_val is not None and abs(api_val) < 0.0001)
        excel_nonzero = (abs(excel_val) > 0.0001)

        # Or significant drift beyond tolerance
        if api_val is not None:
            diff = abs(api_val - excel_val)
        else:
            diff = abs(excel_val)

        needs_fix = (api_is_zero and excel_nonzero) or (diff > GT_TOLERANCE)

        if needs_fix:
            fixes.append({
                "id": row_id,
                "ratio_name": ratio_name,
                "period": period,
                "api_val": api_val,
                "excel_val": excel_val,
                "diff": diff
            })
            stats["fixed"] += 1
        else:
            stats["matched"] += 1

    # ── Report ────────────────────────────────────────────
    print(f"\n[{ticker}] Comparison result:")
    print(f"  ✅ Already correct:     {stats['matched']}")
    print(f"  🔧 Need overwrite:      {stats['fixed']}")
    print(f"  ⚠️  Missing in Excel:   {stats['missing_in_excel']}")

    if fixes:
        print(f"\n  Sample fixes (first 5):")
        for f in fixes[:5]:
            print(f"    [{f['period']}] {f['ratio_name']}: API={f['api_val']:.4f}% → Excel={f['excel_val']:.4f}% (Δ={f['diff']:.4f}%)")

    if dry_run:
        print(f"\n  [DRY RUN] No changes written.")
        return {"ticker": ticker, "stats": stats, "fixes_preview": fixes[:5]}

    # ── Apply fixes: update CFO_CALC_V2 with Excel values ─
    if fixes:
        print(f"\n[{ticker}] Applying {len(fixes)} overwrites to CFO_CALC_V2 records...")
        success = 0
        for f in fixes:
            try:
                sb.table("financial_ratios")\
                    .update({"value": f["excel_val"]})\
                    .eq("id", f["id"])\
                    .execute()
                success += 1
            except Exception as e:
                print(f"  ❌ Failed to update id={f['id']}: {e}")

        print(f"  ✅ Successfully overwritten: {success}/{len(fixes)} records.")
        stats["applied"] = success
    else:
        print(f"\n[{ticker}] ✅ All CFO_CALC_V2 values already match Excel Ground Truth.")

    return {"ticker": ticker, "stats": stats}


# ═══════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════

def run_excel_auditor(ticker: str, filepath: str, dry_run: bool = False,
                      skip_extract: bool = False, skip_validate: bool = False) -> bool:
    """
    Full Phase 6.2 + 6.3 pipeline for one ticker.

    Args:
        ticker:         Stock ticker (e.g. 'MBB')
        filepath:       Path to downloaded Excel file
        dry_run:        If True, print results without writing to Supabase
        skip_extract:   If True, skip Phase 6.2 extraction (use existing V6_EXCEL data)
        skip_validate:  If True, skip Phase 6.3 Ground Truth comparison
    """
    print(f"\n{'='*60}")
    print(f"[V6 Auditor] Ticker: {ticker} | Dry-run: {dry_run}")
    print(f"{'='*60}")

    sector = get_sector(ticker)
    print(f"[{ticker}] Sector: {sector}")

    # ── Phase 6.2: Extract ───────────────────────────────
    if not skip_extract:
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            if not skip_validate:
                print("  Skipping validation too since no Excel file.")
            return False

        try:
            print(f"[{ticker}] Loading Excel sheets (timeout={EXCEL_READ_TIMEOUT}s)...")
            df_bs   = read_excel_with_timeout(filepath, sheet_name="Balance Sheet", header=None)
            xl      = pd.ExcelFile(filepath)
            note_sheet = next((s for s in xl.sheet_names if "note" in s.lower()), None)
            if not note_sheet:
                print(f"❌ Note sheet not found. Available: {xl.sheet_names}")
                return False
            df_note = read_excel_with_timeout(filepath, sheet_name=note_sheet, header=None)
            print(f"[{ticker}] Loaded. BS: {df_bs.shape}, Note: {df_note.shape}")
        except TimeoutError as e:
            print(f"❌ Excel read TIMEOUT (>{EXCEL_READ_TIMEOUT}s): {e}")
            return False
        except Exception as e:
            print(f"❌ Could not read Excel: {e}")
            return False

        # Layout verification — fail loud if Vietcap changes Excel structure
        if sector == "bank":
            if not verify_excel_layout(ticker, df_bs, df_note):
                print(f"❌ [{ticker}] Layout verification failed — aborting extraction to avoid wrong data.")
                return False
            ratios = parse_bank_NPL_CASA(ticker, df_bs, df_note)
        else:
            print(f"[{ticker}] Sector '{sector}' — NPL/CASA not applicable. Skipping extraction.")
            ratios = []

        if ratios:
            print(f"\n[{ticker}] Phase 6.2: {len(ratios)} records calculated.")
            if dry_run:
                print("  [DRY RUN] Sample (first 6):")
                for r in ratios[:6]:
                    print(f"    {r['period']} | {r['ratio_name']}: {r['value']:.2f}{r['unit']}")
            else:
                print(f"[{ticker}] Upserting to Supabase 'financial_ratios'...")
                try:
                    sb.table("financial_ratios")\
                        .upsert(ratios, on_conflict="stock_name,period,ratio_name,source")\
                        .execute()
                    print(f"  ✅ Phase 6.2 Done: {len(ratios)} records upserted.")
                except Exception as e:
                    print(f"  ❌ Upsert error: {e}")
                    return False
        else:
            print(f"⚠️ [{ticker}] No ratios calculated in Phase 6.2.")
    else:
        print(f"[{ticker}] Phase 6.2 skipped (--skip-extract).")

    # ── Phase 6.3: Ground Truth Validate ─────────────────
    if not skip_validate:
        run_ground_truth_validator(ticker, dry_run=dry_run)
    else:
        print(f"[{ticker}] Phase 6.3 skipped (--skip-validate).")

    print(f"\n[{ticker}] ✅ V6 Auditor complete.")
    return True


# ─────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="V6 Excel Auditor — CASA, NPL Extractor + Ground Truth Validator")
    parser.add_argument("--ticker",         default="MBB",  help="Stock ticker, e.g. MBB, VCB")
    parser.add_argument("--file",           default=None,   help="Path to Excel file (default: data/excel_imports/<TICKER>_BCTC_Vietcap.xlsx)")
    parser.add_argument("--dry-run",        action="store_true", help="Print results without writing to Supabase")
    parser.add_argument("--skip-extract",   action="store_true", help="Skip Phase 6.2 extraction, only run validator")
    parser.add_argument("--skip-validate",  action="store_true", help="Skip Phase 6.3 Ground Truth comparison")
    args = parser.parse_args()

    filepath = args.file or str(ROOT / "data" / "excel_imports" / f"{args.ticker}_BCTC_Vietcap.xlsx")
    run_excel_auditor(
        ticker=args.ticker,
        filepath=filepath,
        dry_run=args.dry_run,
        skip_extract=args.skip_extract,
        skip_validate=args.skip_validate
    )
