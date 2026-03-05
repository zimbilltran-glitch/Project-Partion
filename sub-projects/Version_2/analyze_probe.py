import json
import sys

def analyze(ticker):
    filename = f"probe_{ticker}_CASH_FLOW.json"
    print(f"\n--- ANALYZING {ticker} ---")
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        q = data.get("data", {}).get("quarters", [])
        if not q:
            print("No quarter data found.")
            return

        latest = q[0]
        prefix = "cfa" if ticker == "FPT" else ("cfb" if ticker == "MBB" else "cfs")
        
        # Look for the keys with the matching prefix
        keys = sorted([k for k in latest.keys() if k.startswith(prefix)])
        
        # We also want to see if there's any total/summary keys
        for k in keys:
            val = latest[k]
            # Just print a few of them or all? Let's do all, but we need row names.
            # The API response usually has the name in a separate list or something.
            # But here we only have the mapped values.
            print(f"{k}: {val}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze("FPT")
    analyze("MBB")
    analyze("SSI")
