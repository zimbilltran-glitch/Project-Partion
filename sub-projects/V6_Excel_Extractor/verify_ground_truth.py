"""
verify_ground_truth.py -- V6 Data Integrity Audit
===================================================
Cross-reference data on Supabase (what the frontend shows) vs.
Excel Ground Truth downloaded from Vietcap.
Covers: bank (MBB), non-financial (FPT), securities (SSI).

Usage:
    python sub-projects/V6_Excel_Extractor/verify_ground_truth.py
"""
import os, sys, json, math, concurrent.futures
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# -- Path setup ---------------------------------------------------------------
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "sub-projects" / "V2_Data_Pipeline"))

# -- Env + Supabase -----------------------------------------------------------
load_dotenv(dotenv_path=ROOT / ".env")
os.environ['SUPABASE_KEY'] = os.getenv('SUPABASE_SERVICE_ROLE_KEY', os.getenv('SUPABASE_KEY', ''))
from sb_client import get_sb


def read_excel_safe(path: str, timeout: int = 90, **kwargs) -> pd.DataFrame:
    """Timeout-safe pd.read_excel wrapper (CTO hardening rule)."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(pd.read_excel, path, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"read_excel() timed-out ({timeout}s) on {path}")


def verify_ticker(ticker: str, sheet_id: str, table_name: str, excel_sheet_name: str):
    print(f"\n{'='*70}")
    print(f"  Ticker: {ticker}  |  Schema Sheet: {sheet_id}")
    print(f"{'='*70}")

    # 1. Fetch all rows from Supabase for this ticker
    sb = get_sb()
    res = sb.table(table_name).select("*").eq("stock_name", ticker).execute()
    db_data = {row['item_id']: (row.get('periods_data') or {}) for row in res.data}

    if not db_data:
        print(f"  [FAIL] No data found in Supabase for {ticker}")
        return []

    # 2. Load Excel (timeout-safe)
    excel_path = ROOT / "data" / "excel_imports" / f"{ticker}_BCTC_Vietcap.xlsx"
    if not excel_path.exists():
        print(f"  [FAIL] Excel not found: {excel_path}")
        return []

    try:
        df = read_excel_safe(
            str(excel_path), sheet_name=excel_sheet_name,
            skiprows=10, header=0, engine='openpyxl'
        )
    except Exception as e:
        print(f"  [FAIL] {e}")
        return []

    # 3. Create Excel Name -> Row Index Cache
    excel_names = {}
    for i, row_name in enumerate(df.iloc[:, 0]):  # First column usually has names
        if pd.notna(row_name):
            clean_name = str(row_name).strip().lower()
            excel_names[clean_name] = i

    # 4. Load schema to get field information
    schema_path = ROOT / "sub-projects" / "V2_Data_Pipeline" / "golden_schema.json"
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    sector = "bank" if "BANK" in sheet_id else ("sec" if "SEC" in sheet_id else "normal")
    field_mappings = {}
    for fld in schema['fields']:
        if fld['sheet'] == sheet_id:
            vkey = (fld.get('vietcap_key') or {}).get(sector)
            if vkey:
                # Try to find the row index by name instead of using fld['row_number']
                found_row = None
                vn_name_clean = fld['vn_name'].strip().lower()
                
                # Direct match
                if vn_name_clean in excel_names:
                    found_row = excel_names[vn_name_clean]
                else:
                    # Fuzzy / substring match fallback
                    for ex_name, ex_idx in excel_names.items():
                        if vn_name_clean in ex_name or ex_name in vn_name_clean:
                            found_row = ex_idx
                            break
                
                if found_row is not None:
                    field_mappings[fld['field_id']] = {
                        'vn_name': fld['vn_name'],
                        'excel_row': found_row
                    }

    print(f"  Schema fields mapped: {len(field_mappings)} (semantic match) | Supabase rows: {len(db_data)}")

    # 4. Find 2024 column in Excel
    col_2024 = None
    for col in df.columns:
        if str(col).strip() == '2024':
            col_2024 = col
            break

    if col_2024 is None:
        print(f"  [FAIL] 2024 column not found. Cols: {df.columns.tolist()[:8]}")
        return []

    # 5. Compare values
    matches = 0
    mismatches = 0
    missing_in_db = 0
    results = []

    for fid, meta in field_mappings.items():
        try:
            excel_val = df.iloc[meta['excel_row'], df.columns.get_loc(col_2024)]
            if pd.isna(excel_val) or not isinstance(excel_val, (int, float)):
                excel_val = None
        except Exception:
            excel_val = None

        sb_val = db_data.get(fid, {}).get('2024')

        if excel_val is None and (sb_val is None or sb_val == 0.0):
            status = "[OK] EMPTY"
            matches += 1
        elif excel_val is None and sb_val is not None:
            status = "[WARN] EXTRA DATA IN SB"
            mismatches += 1
        elif sb_val is None:
            status = "[FAIL] MISSING IN SB"
            missing_in_db += 1
        else:
            denom = max(abs(excel_val), 1)
            rel_diff = abs(excel_val - sb_val) / denom
            if rel_diff < 0.001:
                status = "[OK] MATCH"
                matches += 1
            else:
                status = f"[FAIL] DRIFT {rel_diff:.2%}"
                mismatches += 1

        results.append({
            'field_id': fid,
            'vn_name': meta['vn_name'][:28],
            'excel_2024': excel_val,
            'sb_2024': sb_val,
            'status': status
        })

    # 6. Print non-OK items
    print(f"\n  {'Field ID':<42} | {'Excel 2024':>16} | {'Supabase':>16} | Status")
    print(f"  {'-'*100}")
    for r in results:
        if '[OK]' not in r['status']:
            e = f"{r['excel_2024']:,.0f}" if r['excel_2024'] is not None else "NULL"
            s = f"{r['sb_2024']:,.0f}" if r['sb_2024'] is not None else "NULL"
            print(f"  {r['field_id']:<42} | {e:>16} | {s:>16} | {r['status']}")

    # 7. Summary
    total = len(results)
    accurate = matches
    acc_pct = round(accurate / total * 100, 1) if total else 0
    print(f"\n  {'-'*70}")
    print(f"  TOTAL={total}  [OK]={matches}  [FAIL DRIFT]={mismatches}  [FAIL MISS]={missing_in_db}")
    print(f"  ACCURACY: {acc_pct}%")

    return results


if __name__ == "__main__":
    print("V6 GROUND TRUTH AUDIT -- Excel vs Supabase")
    print("=" * 70)

    all_results = {}

    # Bank sector (MBB)
    all_results['MBB'] = verify_ticker("MBB", "CDKT_BANK", "balance_sheet_wide", "Balance Sheet")

    # Non-financial sector (FPT)
    all_results['FPT'] = verify_ticker("FPT", "CDKT", "balance_sheet_wide", "Balance Sheet")

    # Securities sector (SSI)
    all_results['SSI'] = verify_ticker("SSI", "CDKT_SEC", "balance_sheet_wide", "Balance Sheet")

    # Grand total
    print(f"\n{'='*70}")
    print("GRAND SUMMARY")
    print(f"{'='*70}")
    for ticker, rows in all_results.items():
        if rows:
            total = len(rows)
            ok = sum(1 for r in rows if '[OK]' in r['status'])
            pct = round(ok / total * 100, 1) if total else 0
            print(f"  {ticker:<6} : {ok}/{total} OK  ->  {pct}% Accuracy")
    print(f"{'='*70}")
