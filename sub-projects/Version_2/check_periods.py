import json

def check_periods(ticker):
    filename = f"probe_{ticker}_CASH_FLOW.json"
    print(f"\n--- {ticker} PERIODS ---")
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        q = data.get("data", {}).get("quarters", [])
        print(f"Total Quarters: {len(q)}")
        for r in q[:10]:
            print(f"Year: {r.get('yearReport')}, Length: {r.get('lengthReport')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_periods("FPT")
    check_periods("MBB")
    check_periods("SSI")
    
