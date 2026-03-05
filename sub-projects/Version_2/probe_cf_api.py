import os
import sys
import json
from pathlib import Path

# Setup paths to include Version_2 for VietcapProvider
V2_PATH = Path(r'c:\Users\Admin\OneDrive\Learn Anything\Antigravity\2.Project v2\sub-projects\Version_2')
sys.path.insert(0, str(V2_PATH))

try:
    from providers.vietcap import VietcapProvider
except ImportError:
    print("Error: Could not import VietcapProvider. Check path.")
    sys.exit(1)

def probe_cf(ticker):
    print(f"\n--- PROBING CASH FLOW FOR: {ticker} ---")
    vc = VietcapProvider()
    
    # Try to fetch raw data directly from the provider's internal method if possible, 
    # or just use the public one and look at the keys if it returns them.
    try:
        data = vc.get_financial_statement(ticker, "CASH_FLOW", is_yearly=True)
        if not data:
            print(f"No data returned for {ticker}")
            return
        
        # We want to see the 'name' and any 'key' or 'id' if present in the items
        print(f"{'Name':<60} | {'Key/ID'}")
        print("-" * 80)
        for item in data:
            # Assuming 'name' exists and we look for 'row_number' or similar 
            # if the provider adds it, or we just look at what we get.
            row_id = item.get('row_number', 'N/A')
            print(f"{item.get('name', 'Unknown'):<60} | {row_id}")
            
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")

def main():
    # Probe one representative from each main sector
    tickers = ["FPT", "MBB", "SSI"]
    for t in tickers:
        probe_cf(t)

if __name__ == "__main__":
    main()
