"""
T1.2 — v5_full_resync.py (ThreadPoolExecutor Version)
Phase 5.5 Performance Tuning: Thay thế vòng lặp subprocess.run bằng ThreadPoolExecutor.

- Import trực tiếp run_pipeline() và sync_ticker() — không tạo thêm Python Interpreter.
- Mỗi ticker chạy Pipeline → Sync tuần tự trong 1 worker thread (tránh race condition API).
- Nhiều ticker chạy song song qua thread pool.
- Estimated speedup: 45 min → 3-5 min với MAX_WORKERS=6-8.

Usage:
    python v5_full_resync.py              # sync tất cả FINSANG_TICKERS từ .env
    python v5_full_resync.py --tickers FPT MBB VHC   # chỉ sync 3 mã cụ thể
    python v5_full_resync.py --workers 4              # giới hạn số workers
"""

import os
import sys
import time
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ── Path + env setup ───────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ROOT / ".env")
except ImportError:
    pass

# ── Import core functions trực tiếp (không subprocess) ────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from pipeline import run_pipeline
from sync_supabase import sync_ticker

# ── Config ─────────────────────────────────────────────────────────────────────
DEFAULT_MAX_WORKERS = 6       # số mã chạy song song (điều chỉnh theo RAM)
DEFAULT_PERIOD_TYPES = ["year", "quarter"]

def process_ticker(ticker: str, period_types: list[str]) -> dict:
    """
    Hàm chạy trong 1 worker thread: pipeline → sync cho 1 ticker.
    Trả về dict kết quả để main thread tổng hợp.
    """
    t_start = time.time()
    status  = "OK"
    error   = ""

    try:
        # Step 1: Fetch API → Normalize → Write Parquet
        print(f"  [{ticker}] Pipeline START")
        run_pipeline(ticker)
        print(f"  [{ticker}] Pipeline DONE")

        # Step 2: Parquet → Supabase upsert + Metrics
        print(f"  [{ticker}] Sync START")
        sync_ticker(ticker, period_types)
        print(f"  [{ticker}] Sync DONE")

    except Exception as e:
        status = "FAIL"
        error  = str(e)
        print(f"  [{ticker}] ERROR: {e}")

    elapsed = time.time() - t_start
    return {"ticker": ticker, "status": status, "elapsed_s": round(elapsed, 1), "error": error}


def main():
    parser = argparse.ArgumentParser(description="Finsang V5 Full Resync (ThreadPool)")
    parser.add_argument("--tickers", nargs="*", default=None,
                        help="Chỉ sync các mã cụ thể. Mặc định: tất cả từ .env")
    parser.add_argument("--workers", type=int, default=DEFAULT_MAX_WORKERS,
                        help=f"Số thread workers song song (default: {DEFAULT_MAX_WORKERS})")
    parser.add_argument("--period",  default="both",
                        choices=["year", "quarter", "both"],
                        help="Period type (default: both)")
    args = parser.parse_args()

    # ── Resolve tickers ────────────────────────────────────────────────────────
    if args.tickers:
        tickers = [t.upper() for t in args.tickers]
    else:
        raw = os.getenv("FINSANG_TICKERS", "")
        tickers = [t.strip() for t in raw.split(",") if t.strip()]

    if not tickers:
        print("ERROR: Khong tim thay tickers. Kiem tra .env FINSANG_TICKERS hoac truyen --tickers.")
        sys.exit(1)

    period_types = ["year", "quarter"] if args.period == "both" else [args.period]
    max_workers  = min(args.workers, len(tickers))  # không tạo thừa workers

    print(f"\n{'='*65}")
    print(f"  FINSANG V5 FULL RESYNC — ThreadPool Mode")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Tickers   : {len(tickers)} mã — {', '.join(tickers)}")
    print(f"  Workers   : {max_workers} threads")
    print(f"  Periods   : {', '.join(period_types)}")
    print(f"{'='*65}\n")

    total_start = time.time()
    results = []

    # ── Chạy song song với ThreadPoolExecutor ─────────────────────────────────
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(process_ticker, ticker, period_types): ticker
            for ticker in tickers
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    # ── Kết quả tổng hợp ──────────────────────────────────────────────────────
    total_elapsed = time.time() - total_start
    ok    = [r for r in results if r["status"] == "OK"]
    fails = [r for r in results if r["status"] != "OK"]

    print(f"\n{'='*65}")
    print(f"  RESYNC COMPLETE")
    print(f"  Total time : {total_elapsed/60:.1f} min ({total_elapsed:.0f}s)")
    print(f"  Success    : {len(ok)}/{len(tickers)}")
    if fails:
        print(f"  FAILURES   : {len(fails)}")
    print(f"\n  Per-ticker breakdown:")
    for r in sorted(results, key=lambda x: x["ticker"]):
        flag = "OK  " if r["status"] == "OK" else "FAIL"
        err  = f"  — {r['error'][:60]}" if r["error"] else ""
        print(f"    [{flag}] {r['ticker']:<6} {r['elapsed_s']:>6.1f}s{err}")
    print(f"{'='*65}\n")

    if fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
