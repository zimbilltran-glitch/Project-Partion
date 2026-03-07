"""
V6 Master Controller — Phase 6.4
==================================
Orchestrates the full V6 pipeline for all bank tickers in VN30:
  1. Read v6_pending_audits.json for pending tickers/periods
  2. Run bot_excel_crawler.py to download Excel files (with throttling)
  3. Run excel_data_auditor.py to extract NPL/CASA and validate Ground Truth
  4. Mark pending entries as "completed" in v6_pending_audits.json

Designed to run monthly (1x/month), usually triggered by scheduler.py
when sync_supabase.py detects a new quarter.

Usage:
  python v6_master_controller.py                # Process all pending
  python v6_master_controller.py --ticker MBB   # Force-run for specific ticker
  python v6_master_controller.py --dry-run      # Simulate without DB writes
  python v6_master_controller.py --all-banks    # Force all VN30 bank tickers
"""

import asyncio
import json
import logging
import os
import sys
import time
import random
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Structured Logging Setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path(__file__).parent.parent.parent / "data" / "v6_controller.log",
            mode="a", encoding="utf-8"
        )
    ]
)
log = logging.getLogger("V6Controller")

ROOT = Path(__file__).parent.parent.parent
V6_DIR = Path(__file__).parent
V6_PENDING_FILE = V6_DIR / "v6_pending_audits.json"
DOWNLOAD_DIR = ROOT / "data" / "excel_imports"

sys.path.insert(0, str(ROOT / "sub-projects" / "V2_Data_Pipeline"))

# Load env for Supabase
load_dotenv(dotenv_path=ROOT / "frontend" / ".env")
URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
KEY = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
if URL: os.environ["SUPABASE_URL"] = URL
if KEY: os.environ["SUPABASE_KEY"] = KEY

# ─────────────────────────────────────────────
# VN30 Bank tickers (source: HSX, as of Q4/2024)
# ─────────────────────────────────────────────
VN30_BANK_TICKERS = [
    "MBB", "VCB", "BID", "CTG", "TCB",
    "ACB", "VPB", "STB", "HDB", "TPB",
    "LPB", "MSB",
]

# ─────────────────────────────────────────────
# Helpers: Pending Audits file management
# ─────────────────────────────────────────────

def load_pending() -> dict:
    if not V6_PENDING_FILE.exists():
        return {"pending": []}
    with open(V6_PENDING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_pending(data: dict) -> None:
    data["_last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(V6_PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def mark_completed(ticker: str, period: str) -> None:
    """Mark a pending entry as completed in v6_pending_audits.json."""
    data = load_pending()
    for entry in data.get("pending", []):
        if entry["ticker"] == ticker and entry["period"] == period:
            entry["status"] = "completed"
            entry["completed_at"] = datetime.now(timezone.utc).isoformat()
    save_pending(data)


def mark_failed(ticker: str, period: str, reason: str) -> None:
    """Mark a pending entry as failed."""
    data = load_pending()
    for entry in data.get("pending", []):
        if entry["ticker"] == ticker and entry["period"] == period:
            entry["status"] = "failed"
            entry["error"] = reason
            entry["failed_at"] = datetime.now(timezone.utc).isoformat()
    save_pending(data)


def get_pending_tickers(data: dict) -> list[str]:
    """Get unique tickers with pending status."""
    tickers = []
    seen = set()
    for entry in data.get("pending", []):
        if entry.get("status") == "pending" and entry["ticker"] not in seen:
            tickers.append(entry["ticker"])
            seen.add(entry["ticker"])
    return tickers


def excel_file_path(ticker: str) -> Path:
    return DOWNLOAD_DIR / f"{ticker}_BCTC_Vietcap.xlsx"


# ─────────────────────────────────────────────
# Phase 1: Download Excel via Playwright Bot
# ─────────────────────────────────────────────

async def download_excel_for_ticker(ticker: str, headless: bool = True) -> bool:
    """Run the Playwright crawler for one ticker. Returns True on success."""
    try:
        from bot_excel_crawler import download_excel
        await download_excel(ticker, headless=headless)
        fpath = excel_file_path(ticker)
        if fpath.exists() and fpath.stat().st_size > 10_000:   # >10KB = valid
            print(f"  ✅ [{ticker}] Excel downloaded: {fpath.name} ({fpath.stat().st_size:,} bytes)")
            return True
        else:
            print(f"  ❌ [{ticker}] Excel file missing or too small after download.")
            return False
    except Exception as e:
        print(f"  ❌ [{ticker}] Download error: {e}")
        return False


# ─────────────────────────────────────────────
# Phase 2: Run Auditor (Extract + Validate)
# ─────────────────────────────────────────────

def run_auditor_for_ticker(ticker: str, dry_run: bool = False) -> bool:
    """Run excel_data_auditor for one ticker. Returns True on success."""
    try:
        from excel_data_auditor import run_excel_auditor
        return run_excel_auditor(
            ticker=ticker,
            filepath=str(excel_file_path(ticker)),
            dry_run=dry_run,
        )
    except Exception as e:
        print(f"  ❌ [{ticker}] Auditor error: {e}")
        return False


# ─────────────────────────────────────────────
# Core: Process one ticker end-to-end
# ─────────────────────────────────────────────

async def process_ticker(ticker: str, pending_periods: list[str],
                         dry_run: bool = False, skip_download: bool = False) -> bool:
    ticker = ticker.upper()
    log.info("="*60)
    log.info(f"Processing ticker: {ticker} | Periods: {pending_periods}")
    log.info("="*60)

    # Step 1: Download Excel (skip if file already exists and fresh)
    fpath = excel_file_path(ticker)
    if skip_download and fpath.exists():
        print(f"  [Download] Skipping — file exists: {fpath.name}")
        download_ok = True
    else:
        print(f"  [Download] Starting Playwright bot for {ticker}...")
        download_ok = await download_excel_for_ticker(ticker)

    if not download_ok:
        for p in pending_periods:
            mark_failed(ticker, p, "excel_download_failed")
        return False

    # Step 2: Run Auditor (Phase 6.2 + 6.3)
    print(f"\n  [Auditor] Running Excel Auditor for {ticker}...")
    audit_ok = run_auditor_for_ticker(ticker, dry_run=dry_run)

    if audit_ok:
        if not dry_run:
            for p in pending_periods:
                mark_completed(ticker, p)
        print(f"  ✅ [{ticker}] All steps completed successfully.")
    else:
        for p in pending_periods:
            mark_failed(ticker, p, "auditor_failed")
        print(f"  ❌ [{ticker}] Auditor failed.")

    return audit_ok


# ─────────────────────────────────────────────
# Main Orchestrator
# ─────────────────────────────────────────────

async def main_async(args):
    print(f"\n{'='*60}")
    print(f"[V6 Master Controller] Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    print(f"{'='*60}\n")

    # Determine which tickers to process
    if args.all_banks:
        tickers_to_process = {t: [] for t in VN30_BANK_TICKERS}
        print(f"  Mode: --all-banks → forcing all {len(VN30_BANK_TICKERS)} VN30 bank tickers")
    elif args.all_db_banks:
        from sb_client import get_sb
        sb = get_sb()
        db_bank_tickers = []
        for t in VN30_BANK_TICKERS:
            # Check if this ticker exists in the DB
            res = sb.table("balance_sheet").select("stock_name").eq("stock_name", t).limit(1).execute()
            if res.data:
                db_bank_tickers.append(t)
        
        tickers_to_process = {t: [] for t in db_bank_tickers}
        print(f"  Mode: --all-db-banks → forcing {len(db_bank_tickers)} bank tickers found in DB: {db_bank_tickers}")
    elif args.ticker:
        tickers_to_process = {args.ticker.upper(): []}
        print(f"  Mode: --ticker {args.ticker.upper()} → forcing single ticker")
    else:
        # Read from pending_audits file
        pending_data = load_pending()
        pending_list = pending_data.get("pending", [])
        pending_entries = [e for e in pending_list if e.get("status") == "pending"]

        if not pending_entries:
            print("  ✅ No pending audits found in v6_pending_audits.json. Nothing to do.")
            return

        # Group by ticker
        tickers_to_process: dict[str, list[str]] = {}
        for entry in pending_entries:
            t = entry["ticker"]
            p = entry["period"]
            tickers_to_process.setdefault(t, []).append(p)

        print(f"  Pending tickers ({len(tickers_to_process)}): {list(tickers_to_process.keys())}")

    # Process each ticker with throttling
    total = len(tickers_to_process)
    success_count = 0

    for i, (ticker, periods) in enumerate(tickers_to_process.items(), 1):
        print(f"\n  [{i}/{total}] Processing {ticker}...")

        ok = await process_ticker(
            ticker=ticker,
            pending_periods=periods,
            dry_run=args.dry_run,
            skip_download=args.skip_download,
        )
        if ok:
            success_count += 1

        # Throttle between tickers to avoid Cloudflare / anti-bot
        if i < total:
            delay = random.randint(10, 20)
            print(f"\n  💤 Throttle: waiting {delay}s before next ticker...")
            await asyncio.sleep(delay)

    print(f"\n{'='*60}")
    print(f"[V6 Master Controller] FINISHED")
    print(f"  Processed: {total} tickers | Success: {success_count} | Failed: {total - success_count}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="V6 Master Controller — Monthly Excel Audit for Bank VN30")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ticker",      help="Force-run for a specific ticker (e.g. MBB)")
    group.add_argument("--all-banks",   action="store_true", help=f"Force-run all {len(VN30_BANK_TICKERS)} VN30 bank tickers")
    group.add_argument("--all-db-banks",action="store_true", help="Force-run all bank tickers present in Supabase DB")
    parser.add_argument("--dry-run",    action="store_true", help="Simulate without writing to Supabase")
    parser.add_argument("--skip-download", action="store_true", help="Skip Playwright download if Excel file already exists")
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
