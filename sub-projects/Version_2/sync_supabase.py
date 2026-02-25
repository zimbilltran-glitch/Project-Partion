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
  python Version_2/sync_supabase.py --ticker VHC
  python Version_2/sync_supabase.py --ticker FPT --period year
  python Version_2/sync_supabase.py --all          # all FINSANG_TICKERS
"""

import argparse, os, sys, json, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
from datetime import datetime

# ── allow running from project root ───────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
except ImportError:
    pass

import math
from pipeline import load_tab, DATA_DIR
from metrics import calc_metrics

# ─── Config ───────────────────────────────────────────────────────────────────
# Supabase long-format table mapping
SHEET_TO_TABLE = {
    "cdkt":  "balance_sheet",
    "kqkd":  "income_statement",
    "lctt":  "cash_flow",
    "cstc":  "financial_ratios",
}

SOURCE_TAG = "vietcap"

# ─── Supabase Client ──────────────────────────────────────────────────────────
def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("  ❌ SUPABASE_URL / SUPABASE_KEY not set in .env")
        sys.exit(1)
    try:
        from supabase import create_client
        return create_client(url, key)
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

    # Map sheet_id to row_number via row order in DataFrame (V2 preserves schema order)
    for row_idx, (_, row) in enumerate(df.iterrows(), start=1):
        field_id = str(row.get("field_id", ""))
        item     = str(row.get("vn_name", ""))
        unit_val = str(row.get("unit", "tỷ đồng"))
        level    = int(row.get("level", 0))

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
                "row_number": row_idx,
                "period":     period_col,
                "unit":       unit_val,
                "value":      numeric_val,
            })
    return rows


def build_ratio_rows(df, ticker: str, period_type: str) -> list[dict]:
    """Transform metrics DataFrame into financial_ratios rows."""
    rows = []
    period_cols = [c for c in df.columns if c not in ("field_id", "vn_name", "unit", "level")]

    for _, row in df.iterrows():
        ratio_name = str(row.get("vn_name", ""))
        for period_col in period_cols:
            val = row.get(period_col)
            if val is None:
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

    # Step 2: For each sheet × period, load Parquet and upload
    sheets = ["cdkt", "kqkd", "lctt"]
    for period_type in period_types:
        for sheet in sheets:
            if not parquet_exists(ticker, period_type, sheet):
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
