"""
Phase T — Trigger: Multi-Ticker Runner
run_all.py — Run the pipeline for all tickers defined in FINSANG_TICKERS (.env)

Usage:
  python Version_2/run_all.py                     # uses FINSANG_TICKERS from .env
  python Version_2/run_all.py --tickers VHC FPT   # override with CLI args
  python Version_2/run_all.py --tickers VHC --dry-run  # show tickers, no run

Design:
  - Reads FINSANG_TICKERS from .env (comma-separated)
  - Runs each ticker sequentially (API rate-limit safe)
  - Prints a final summary table: ticker | sections OK | status | duration
  - Logs all runs to pipeline.log (via pipeline.log_run())
  - Logs to Supabase pipeline_runs (via log_supabase(), graceful on failure)
"""

import argparse, os, sys, time
from pathlib import Path
from datetime import datetime

# ── Bootstrap: resolve project root ──────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "Version_2"))

# Load .env early before importing pipeline (which also loads it, but be safe)
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ROOT / ".env")
except ImportError:
    pass

from pipeline import run_pipeline

# ─── CLI ──────────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="Finsang V2.0 — Multi-Ticker Runner")
    parser.add_argument(
        "--tickers", nargs="+",
        help="Override tickers (space-separated). Default: FINSANG_TICKERS from .env"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print ticker list without running pipeline"
    )
    return parser.parse_args()

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()

    # Resolve ticker list
    if args.tickers:
        tickers = [t.upper() for t in args.tickers]
    else:
        raw = os.getenv("FINSANG_TICKERS", "VHC")
        tickers = [t.strip().upper() for t in raw.split(",") if t.strip()]

    print(f"\n{'━'*60}")
    print(f"  🦁 FINSANG V2.0 — Multi-Ticker Runner")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Tickers ({len(tickers)}): {', '.join(tickers)}")
    print(f"{'━'*60}\n")

    if args.dry_run:
        print("  [DRY RUN] — No pipeline execution. Tickers listed above.")
        return

    # Run each ticker sequentially
    results = []
    for i, ticker in enumerate(tickers, 1):
        print(f"\n  [{i}/{len(tickers)}] Starting: {ticker}")
        t_start = time.time()
        try:
            run_pipeline(ticker)
            elapsed = time.time() - t_start
            results.append({"ticker": ticker, "status": "✅ OK", "elapsed": f"{elapsed:.1f}s"})
        except Exception as e:
            elapsed = time.time() - t_start
            results.append({"ticker": ticker, "status": f"❌ {e}", "elapsed": f"{elapsed:.1f}s"})
            print(f"  ❌ {ticker} failed: {e}")

    # Summary table
    print(f"\n{'━'*60}")
    print(f"  SUMMARY ({datetime.now().strftime('%H:%M:%S')})")
    print(f"{'━'*60}")
    for r in results:
        print(f"  {r['ticker']:<8} {r['status']:<20} {r['elapsed']}")
    print(f"{'━'*60}\n")


if __name__ == "__main__":
    main()
