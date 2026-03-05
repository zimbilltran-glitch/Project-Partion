"""
T1.4 Benchmark — Đo thời gian pipeline-only (bỏ qua Supabase sync)
Chạy run_pipeline() cho danh sách tickers với ThreadPoolExecutor.
Không cần SUPABASE_URL/KEY (chỉ fetch API + write Parquet).
"""
import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ROOT / ".env")
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent / "Version_2"))
from pipeline import run_pipeline

# VN30 tickers đầy đủ (31 mã)
VN30_TICKERS = [
    "ACB","BCM","BID","BVH","CTG",
    "FPT","GAS","GVR","HDB","HPG",
    "MBB","MSN","MWG","PLX","POW",
    "SAB","SHB","SSB","SSI","STB",
    "TCB","TPB","VCB","VHC","VHM",
    "VIB","VIC","VJC","VND","VNM",
    "VPB"
]

MAX_WORKERS = 6

def pipeline_only(ticker: str) -> dict:
    t_start = time.time()
    status = "OK"
    error = ""
    try:
        run_pipeline(ticker)
    except Exception as e:
        status = "FAIL"
        error = str(e)
    elapsed = time.time() - t_start
    return {"ticker": ticker, "status": status, "elapsed_s": round(elapsed, 1), "error": error}

def main():
    tickers = VN30_TICKERS
    print(f"\n{'='*65}")
    print(f"  T1.4 BENCHMARK — Pipeline Only (No Supabase)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Tickers : {len(tickers)} mã VN30")
    print(f"  Workers : {MAX_WORKERS} threads")
    print(f"{'='*65}\n")

    total_start = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(pipeline_only, t): t for t in tickers}
        done = 0
        for future in as_completed(futures):
            r = future.result()
            results.append(r)
            done += 1
            flag = "OK  " if r["status"] == "OK" else "FAIL"
            print(f"  [{done:>2}/{len(tickers)}] [{flag}] {r['ticker']:<6} {r['elapsed_s']:>6.1f}s")

    total_elapsed = time.time() - total_start
    ok    = [r for r in results if r["status"] == "OK"]
    fails = [r for r in results if r["status"] != "OK"]

    avg = sum(r["elapsed_s"] for r in results) / len(results)

    print(f"\n{'='*65}")
    print(f"  BENCHMARK RESULT")
    print(f"  Wall time  : {total_elapsed/60:.1f} min ({total_elapsed:.1f}s)")
    print(f"  Avg/ticker : {avg:.1f}s")
    print(f"  Success    : {len(ok)}/{len(tickers)}")
    if fails:
        print(f"  FAILURES   :")
        for r in fails:
            print(f"    {r['ticker']}: {r['error'][:80]}")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    main()
