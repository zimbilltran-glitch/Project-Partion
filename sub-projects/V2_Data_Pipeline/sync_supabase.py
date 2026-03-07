"""
Phase S+T — Sync: V2 Parquet → Supabase Cloud Bridge
sync_supabase.py

Role: @data-engineering-data-pipeline + @data-engineer + @data-scientist
Supervised by: @cto-mentor-supervisor

Reads encrypted Parquet files written by pipeline.py and upserts
the data into the existing Supabase financial statement tables:
  balance_sheet    ← CDKT (Cân Đối Kế Toán)
  income_statement ← KQKD (Kết Quả Kinh Doanh)
  cash_flow        ← LCTT (Lưu Chuyển Tiền Tệ)
  financial_ratios ← CSTC (Chỉ Số Tài Chính)

Data model: long-format (one row per ticker × period × field)
The *_wide views in Supabase automatically pivot these via jsonb_object_agg.

Usage:
  python V2_Data_Pipeline/sync_supabase.py --ticker VHC
  python V2_Data_Pipeline/sync_supabase.py --ticker FPT --period year
  python V2_Data_Pipeline/sync_supabase.py --all          # all FINSANG_TICKERS
"""

import argparse, os, sys, json, warnings, pandas as pd
warnings.filterwarnings("ignore")
from pathlib import Path
from datetime import datetime, timezone

# V6 integration
V6_PENDING_FILE = Path(__file__).parent.parent / "V6_Excel_Extractor" / "v6_pending_audits.json"
BANK_SECTORS    = {"bank"}   # sectors that require Excel audit for NPL/CASA

# ── allow running from project root ───────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

import math
from pipeline import load_tab, DATA_DIR
from metrics import calc_metrics
from sector import get_sector

# ─── Config ───────────────────────────────────────────────────────────────────
# Supabase long-format table mapping (all sector variants → same tables)
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

# Sector → sheets to sync
SECTOR_SHEETS = {
    "bank":   ["cdkt_bank", "kqkd_bank", "lctt_bank"],
    "sec":    ["cdkt_sec",  "kqkd_sec",  "lctt_sec"],
    "normal": ["cdkt",      "kqkd",      "lctt"],
}

SOURCE_TAG = "vietcap"

# ─── Load Environment ──────────────────────────────────────────────────────────
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
url = os.getenv("SUPABASE_URL")
# Use the backend service role key to bypass RLS for writes
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not url or not key:
    print(f"❌ Error: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not valid from {env_path}")
    print("Cannot write to DB without service_role key.")
    sys.exit(1)
else:
    # Ensure these are set in the environment for subsequent calls
    os.environ["SUPABASE_URL"] = url
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = key

# ─── Supabase Client ──────────────────────────────────────────────────────────
def get_supabase():
    # URL and KEY are already loaded into os.environ and checked
    try:
        from supabase import create_client
        return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    except ImportError:
        print("  ❌ supabase-py not installed: pip install supabase")
        sys.exit(1)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def parquet_exists(ticker: str, period_type: str, sheet: str) -> bool:
    p = DATA_DIR / ticker.upper() / f"period_type={period_type}" / f"sheet={sheet}" / f"{ticker.upper()}.parquet"
    return p.exists()


def build_rows_for_sheet(df, ticker: str, sheet_id: str, period_type: str) -> list[dict]:
    """Transform V2 long-format DataFrame into list of dicts for Supabase upsert."""
    rows = []
    period_cols = [c for c in df.columns if c not in ("field_id", "vn_name", "unit", "level")]

    # Map sheet_id to row_number via schema-defined row_number (V2 stores this in sheet_row_idx)
    for _, row in df.iterrows():
        field_id = str(row.get("field_id", ""))
        item     = str(row.get("vn_name", ""))
        unit_val = str(row.get("unit", "tỷ đồng"))
        level    = int(row.get("level", 0))
        
        # Use schema's row_number if available, fallback to 999 (custom additions)
        row_num  = int(row.get("sheet_row_idx", 999))

        for period_col in period_cols:
            val = row.get(period_col)
            if val is None:
                continue
            try:
                numeric_val = float(val)
            except (TypeError, ValueError):
                continue
            # Reject NaN/Inf — not JSON-serializable
            if not math.isfinite(numeric_val):
                continue

            # Normalize period format: "Q4/2024" → keep as-is; "2024" → year format
            rows.append({
                "stock_name": ticker.upper(),
                "asset_type": "STOCK",
                "source":     SOURCE_TAG,
                "item_id":    field_id,
                "item":       item,
                "levels":     level,
                "row_number": row_num,
                "period":     period_col,
                "unit":       unit_val,
                "value":      numeric_val,
            })
    return rows


def build_ratio_rows(df, ticker: str, period_type: str) -> list[dict]:
    """Transform metrics DataFrame into financial_ratios rows."""
    rows = []
    meta_cols = ("item_id", "vn_name", "unit", "level", "row_number")
    period_cols = [c for c in df.columns if c not in meta_cols]

    for _, row in df.iterrows():
        ratio_name = str(row.get("vn_name", ""))
        item_id = str(row.get("item_id", ""))
        unit = str(row.get("unit", ""))
        level = int(row.get("level", 0))
        row_num = int(row.get("row_number", 0))

        for period_col in period_cols:
            val = row.get(period_col)
            if val is None or pd.isna(val):
                continue
            try:
                numeric_val = float(val)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(numeric_val):
                continue

            rows.append({
                "stock_name": ticker.upper(),
                "asset_type": "STOCK",
                "ratio_name": ratio_name,
                "period":     period_col,
                "value":      numeric_val,
                "source":     "CFO_CALC_V2",
                "item_id":    item_id,
                "levels":     level,
                "row_number": row_num,
                "unit":       unit,
            })
    return rows


# ─── Purge existing ticker data before upsert ─────────────────────────────────
def purge_ticker(sb, ticker: str) -> None:
    """Remove all existing rows for this ticker before fresh upsert (idempotent)."""
    tables = list(SHEET_TO_TABLE.values())
    for tbl in tables:
        resp = sb.table(tbl).delete().eq("stock_name", ticker.upper()).execute()
        deleted = len(resp.data) if resp.data else 0
        print(f"    🗑️  Purged {deleted:>5} rows from {tbl} for {ticker}")


# ─── Core Upload ──────────────────────────────────────────────────────────────
def upsert_rows(sb, table: str, rows: list[dict], batch_size: int = 500) -> int:
    """Batch upsert rows into a Supabase table. Returns total rows inserted."""
    if not rows:
        return 0
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        sb.table(table).insert(batch).execute()
        total += len(batch)
    return total


# ─── Main sync per ticker ─────────────────────────────────────────────────────
def sync_ticker(ticker: str, period_types: list[str] = ("year", "quarter")):
    print(f"\n{'═'*60}")
    print(f"  FINSANG SYNC v2.0 — {ticker.upper()}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Source: Vietcap Parquet")
    print(f"{'═'*60}\n")

    sb = get_supabase()

    # Step 1: Purge existing data for this ticker (idempotent)
    print(f"  ▶ Step 1: Purging existing data for {ticker}...")
    purge_ticker(sb, ticker)

    # Step 2: Determine sector-specific sheets for this ticker
    sector = get_sector(ticker)
    sheets = SECTOR_SHEETS.get(sector, SECTOR_SHEETS["normal"])
    print(f"  ▶ Sector: {sector} → sheets: {sheets}")

    for period_type in period_types:
        for sheet in sheets:
            if not parquet_exists(ticker, period_type, sheet):
                # Fallback: try generic sheet if sector-specific not found
                generic = sheet.split('_')[0]  # cdkt_bank → cdkt
                if generic != sheet and parquet_exists(ticker, period_type, generic):
                    print(f"    ⚠️  No {sheet} Parquet, falling back to {generic}")
                    sheet = generic
                else:
                    print(f"    ⚠️  No Parquet found: {ticker}/{period_type}/{sheet} — run pipeline first")
                    continue

            print(f"  ▶ Loading {ticker} / {sheet.upper()} / {period_type} ...")
            try:
                df = load_tab(ticker, period_type, sheet)
            except FileNotFoundError as e:
                print(f"    ❌ load_tab failed: {e}")
                continue

            if df.empty:
                print(f"    ⚠️  Empty DataFrame for {ticker}/{sheet}/{period_type}")
                continue

            rows = build_rows_for_sheet(df, ticker, SHEET_TO_TABLE[sheet], period_type)
            tbl  = SHEET_TO_TABLE[sheet]
            count = upsert_rows(sb, tbl, rows)
            print(f"    ✅ Uploaded {count:>5} rows → {tbl} ({period_type})")
    # Step 3: Financial ratios (derived metrics from metrics.py)
    print(f"\n  ▶ Step 3: Syncing derived metrics (CSTC) ...")
    for period_type in period_types:
        try:
            metrics_df = calc_metrics(ticker, period_type)
        except Exception as e:
            print(f"    ⚠️  calc_metrics failed ({period_type}): {e}")
            continue

        if metrics_df.empty:
            print(f"    ⚠️  No metrics for {ticker}/{period_type}")
            continue

        ratio_rows = build_ratio_rows(metrics_df, ticker, period_type)
        count = upsert_rows(sb, "financial_ratios", ratio_rows)
        print(f"    ✅ Uploaded {count:>5} rows → financial_ratios ({period_type})")

    print(f"\n  🎯 Sync complete for {ticker.upper()}\n")

    # ── V6 Trigger: detect new quarters → flag for Excel audit ──────────────
    if sector in BANK_SECTORS:
        _v6_trigger_check(sb, ticker, ratio_rows if 'ratio_rows' in dir() else [])


def _v6_trigger_check(sb, ticker: str, synced_period_rows: list) -> None:
    """
    V6 Trigger (Phase 6.4):
    After syncing a bank ticker, check if any quarter periods are NEW
    (not yet audited via V6_EXCEL). If so, add them to v6_pending_audits.json.
    """
    # Collect periods just synced
    synced_quarters = set()
    for row in synced_period_rows:
        p = row.get("period", "")
        if p.startswith("Q"):   # e.g. Q4/2024
            synced_quarters.add(p)

    if not synced_quarters:
        return

    # Fetch periods already audited by V6_EXCEL for this ticker
    try:
        existing = sb.table("financial_ratios")\
            .select("period")\
            .eq("stock_name", ticker.upper())\
            .eq("source", "V6_EXCEL")\
            .execute()
        audited_periods = {r["period"] for r in existing.data} if existing.data else set()
    except Exception as e:
        print(f"  ⚠️  V6 Trigger: could not fetch audited periods: {e}")
        return

    new_periods = synced_quarters - audited_periods
    if not new_periods:
        print(f"  ✅ V6 Trigger: {ticker} — all periods already audited.")
        return

    print(f"  🔔 V6 Trigger: {ticker} has {len(new_periods)} new periods needing Excel audit: {sorted(new_periods)}")

    # Load current pending file
    pending_data = {"pending": []}
    if V6_PENDING_FILE.exists():
        try:
            with open(V6_PENDING_FILE, "r", encoding="utf-8") as f:
                pending_data = json.load(f)
        except Exception:
            pass

    existing_keys = {(e["ticker"], e["period"]) for e in pending_data.get("pending", [])}

    added = 0
    for period in sorted(new_periods):
        if (ticker.upper(), period) not in existing_keys:
            pending_data["pending"].append({
                "ticker": ticker.upper(),
                "period": period,
                "requires_excel_audit": True,
                "status": "pending",
                "flagged_at": datetime.now(timezone.utc).isoformat()
            })
            added += 1

    if added:
        pending_data["_last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(V6_PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(pending_data, f, ensure_ascii=False, indent=2)
        print(f"  📝 V6 Trigger: Added {added} new pending entry/entries to {V6_PENDING_FILE.name}")


# ─── Entry point ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Finsang V2 → Supabase Sync")
    parser.add_argument("--ticker", default=None,   help="Single ticker (e.g. VHC)")
    parser.add_argument("--all",    action="store_true", help="Sync all FINSANG_TICKERS")
    parser.add_argument("--period", default="both",
                        choices=["year", "quarter", "both"],
                        help="Period type to sync (default: both)")
    args = parser.parse_args()

    period_types = ["year", "quarter"] if args.period == "both" else [args.period]

    if args.all:
        raw = os.getenv("FINSANG_TICKERS", "VHC")
        tickers = [t.strip() for t in raw.split(",") if t.strip()]
    elif args.ticker:
        tickers = [args.ticker.upper()]
    else:
        print("Usage: sync_supabase.py --ticker VHC  OR  --all")
        sys.exit(1)

    print(f"\n  Tickers to sync: {', '.join(tickers)}")
    print(f"  Period types:    {', '.join(period_types)}\n")

    for ticker in tickers:
        try:
            sync_ticker(ticker, period_types)
        except Exception as e:
            print(f"\n  ❌ SYNC FAILED for {ticker}: {e}\n")


if __name__ == "__main__":
    main()
