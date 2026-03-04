"""
V5 Phase 3 — P3.3: Run pipeline for VN30 tickers + sync to Supabase.
"""
import sys, os, time
from pathlib import Path

# Setup paths
V2 = Path(r'd:\Project_partial\Finsang\sub-projects\Version_2')
sys.path.insert(0, str(V2))

from pipeline import run_pipeline
from providers.vietcap import VietcapProvider

# VN30 tickers (representative subset — full VN30 list)
VN30 = [
    "FPT", "VNM", "VCB", "VHM", "HPG",
    "MBB", "TCB", "VPB", "BID", "CTG",
    "SSI", "HCM", "VCI", "VND", "SHS",
    "MSN", "MWG", "VRE", "PLX", "GAS",
    "SAB", "ACB", "STB", "TPB", "SHB",
    "POW", "BCM", "GVR", "PDR", "KDH",
]

provider = VietcapProvider()
results = []

for i, ticker in enumerate(VN30):
    print(f"\n{'='*60}")
    print(f"  [{i+1}/{len(VN30)}] Processing {ticker}")
    print(f"{'='*60}")
    try:
        run_pipeline(ticker, provider=provider)
        results.append((ticker, "OK"))
    except Exception as e:
        results.append((ticker, f"FAIL: {e}"))
        print(f"  ERROR: {e}")
    
    time.sleep(1)  # Rate limiting

# Summary
print(f"\n{'='*60}")
print(f"  PIPELINE SUMMARY ({len(VN30)} tickers)")
print(f"{'='*60}")
ok = sum(1 for _, s in results if s == "OK")
fail = len(results) - ok
print(f"  OK: {ok} | FAIL: {fail}")
for ticker, status in results:
    if status != "OK":
        print(f"  ❌ {ticker}: {status}")

# Write results
with open(Path(r'd:\Project_partial\Finsang\sub-projects\V5_improdata\_pipeline_batch_results.txt'), 'w', encoding='utf-8') as f:
    f.write(f"Pipeline batch run: {len(VN30)} tickers\n")
    f.write(f"OK: {ok} | FAIL: {fail}\n\n")
    for ticker, status in results:
        f.write(f"{ticker}: {status}\n")
