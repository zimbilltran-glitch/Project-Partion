"""
V3 Phase P1.1 — Fetch OHLCV VN30 (2025→2026)
=============================================
Script này fetch dữ liệu giá lịch sử (OHLCV) cho tất cả tickers VN30
từ vnstock (VCI source), sau đó upsert vào Supabase table `stock_ohlcv`.

API: vnstock library (VCI data source — tested, working)
fallback: TCBS source

Usage:
    cd Finsang/sub-projects/V3_SimplyWallSt/scripts/
    python fetch_ohlcv_vn30.py                    # Tất cả VN30
    python fetch_ohlcv_vn30.py --ticker VHC        # 1 ticker
    python fetch_ohlcv_vn30.py --dry-run           # Check dữ liệu, không ghi DB

Rate limit: 0.5s delay giữa mỗi ticker (~15s total)
Scope: 2025-01-01 → ngày hiện tại
Expected: ~300-400 rows per ticker, ~9,000-12,000 rows total
"""

import os
import sys
import time
import argparse
from datetime import date
from pathlib import Path

# ─── Load .env ─────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# ─── Add Version_2 to path for sector.py ────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Version_2"))
from sector import get_all_tickers

# ─── Config ──────────────────────────────────────────────────────────────────
START_DATE  = "2025-01-01"
END_DATE    = date.today().strftime("%Y-%m-%d")
RATE_DELAY  = 0.5   # seconds between ticker requests

# ─── Fetch OHLCV via vnstock ──────────────────────────────────────────────────
def fetch_ohlcv_vnstock(ticker: str,
                         start: str = START_DATE,
                         end: str   = END_DATE) -> list[dict]:
    """
    Fetch OHLCV rows for a ticker via vnstock (VCI source, fallback TCBS).
    Returns list of dicts ready for Supabase upsert.
    """
    try:
        from vnstock import Vnstock
    except ImportError:
        raise ImportError("Run: pip install vnstock")

    rows = []

    # Try VCI source first, then TCBS
    for source in ["VCI", "TCBS"]:
        try:
            s  = Vnstock().stock(symbol=ticker, source=source)
            df = s.quote.history(start=start, end=end, interval="1D")
            if df is not None and len(df) > 0:
                break
        except Exception:
            df = None
            continue

    if df is None or len(df) == 0:
        return []

    for _, row in df.iterrows():
        trade_time = row["time"]
        # Normalize to ISO string with TZ
        if hasattr(trade_time, "strftime"):
            time_str = trade_time.strftime("%Y-%m-%dT00:00:00+07:00")
        else:
            time_str = str(trade_time)[:10] + "T00:00:00+07:00"

        rows.append({
            "stock_name": ticker.upper(),
            "time":       time_str,
            "open":       float(row["open"])   if row["open"]   is not None else None,
            "high":       float(row["high"])   if row["high"]   is not None else None,
            "low":        float(row["low"])    if row["low"]    is not None else None,
            "close":      float(row["close"])  if row["close"]  is not None else None,
            "volume":     float(row["volume"]) if row["volume"] is not None else None,
            "asset_type": "STOCK",
        })

    return rows


# ─── Upsert to Supabase ───────────────────────────────────────────────────────
def upsert_ohlcv(rows: list[dict], dry_run: bool = False) -> int:
    """
    Upsert rows to Supabase stock_ohlcv table.
    PK = (stock_name, time) — duplicate dates are overwritten.
    Returns number of rows upserted.
    """
    if dry_run:
        print(f"    [DRY RUN] Would upsert {len(rows)} rows")
        return len(rows)

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY not in environment")

    try:
        from supabase import create_client
    except ImportError:
        raise ImportError("Run: pip install supabase")

    sb = create_client(url, key)

    # Batch upsert in chunks of 200 (Supabase limit)
    CHUNK = 200
    total_upserted = 0
    for i in range(0, len(rows), CHUNK):
        chunk = rows[i:i + CHUNK]
        sb.table("stock_ohlcv").upsert(
            chunk,
            on_conflict="stock_name,time"
        ).execute()
        total_upserted += len(chunk)

    return total_upserted


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="V3 P1.1 — Fetch OHLCV VN30 and upsert to Supabase"
    )
    parser.add_argument("--ticker",   help="Single ticker (default: all VN30)")
    parser.add_argument("--start",    default=START_DATE, help="Start date YYYY-MM-DD")
    parser.add_argument("--end",      default=END_DATE,   help="End date YYYY-MM-DD")
    parser.add_argument("--dry-run",  action="store_true", help="Fetch but don't write to Supabase")
    args = parser.parse_args()

    # Choose tickers
    if args.ticker:
        tickers = [args.ticker.upper()]
    else:
        tickers = get_all_tickers(vn30_only=True)
        print(f"Found {len(tickers)} VN30 tickers: {', '.join(tickers)}")

    print(f"\n{'='*60}")
    print(f"  Finsang V3 — OHLCV Fetcher")
    print(f"  Date range: {args.start} → {args.end}")
    print(f"  Tickers:    {len(tickers)}")
    print(f"  Mode:       {'DRY RUN' if args.dry_run else 'WRITE TO SUPABASE'}")
    print(f"{'='*60}\n")

    total_rows = 0
    failed = []

    for i, ticker in enumerate(tickers, 1):
        print(f"  [{i:>2}/{len(tickers)}] {ticker} ... ", end="", flush=True)

        rows = fetch_ohlcv_vnstock(ticker, start=args.start, end=args.end)

        if not rows:
            print(f"⚠️  No data returned")
            failed.append(ticker)
            continue

        try:
            n = upsert_ohlcv(rows, dry_run=args.dry_run)
            print(f"✅ {n} rows ({rows[0]['time'][:10]} → {rows[-1]['time'][:10]})")
            total_rows += n
        except Exception as e:
            print(f"❌ Upsert failed: {e}")
            failed.append(ticker)

        if i < len(tickers):
            time.sleep(RATE_DELAY)

    # Summary
    print(f"\n{'='*60}")
    print(f"  ✅ Success: {len(tickers) - len(failed)} tickers, {total_rows:,} rows")
    if failed:
        print(f"  ❌ Failed:  {', '.join(failed)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
