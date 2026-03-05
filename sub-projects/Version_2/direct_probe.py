import requests
import json
import os
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://trading.vietcap.com.vn/",
    "Origin": "https://trading.vietcap.com.vn",
}

BASE_URL = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/financial-statement?section={section}"

def probe(ticker, section):
    url = BASE_URL.format(ticker=ticker.upper(), section=section)
    print(f"\n--- PROBING {ticker} | {section} ---")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        
        # Save to file for manual inspection if needed
        filename = f"probe_{ticker}_{section}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved raw response to {filename}")
        
        # Print summary of the structure
        if data.get("successful"):
            records = data.get("data", {}).get("quarters", [])
            if not records:
                records = data.get("data", {}).get("years", [])
            
            if records:
                print(f"Found {len(records)} periods.")
                first_row = records[0]
                # Filter keys that are likely row keys (starts with cfa, cfb, etc.)
                row_keys = sorted([k for k in first_row.keys() if any(k.startswith(p) for p in ["cfa", "cfb", "cfs", "cfi"])])
                print(f"Detected {len(row_keys)} potential row keys: {row_keys[:10]} ...")
            else:
                print("No period data found in response.")
        else:
            print(f"API returned failure: {data.get('msg')}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Test one of each type
    probe("FPT", "CASH_FLOW")
    probe("MBB", "CASH_FLOW")
    probe("SSI", "CASH_FLOW")
