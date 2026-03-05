import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def fetch_and_print(ticker, section):
    url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/financial-statement?section={section}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://trading.vietcap.com.vn/",
        "Origin": "https://trading.vietcap.com.vn"
    }
    r = requests.get(url, headers=headers, timeout=10)
    data = r.json()
    if "data" in data :
         rows = data["data"]
         years = rows.get("years", [])
         if len(years) > 0:
             recent = sorted(years, key=lambda x: x.get("yearReport", 0), reverse=True)[0]
             print(f"\n--- {ticker} - {section} {recent.get('yearReport')} ---")
             for k in sorted([k for k in recent.keys() if k.startswith("isa")], key=lambda x: int(x.replace("isa","")) if x.replace("isa","").isdigit() else 999):
                 print(f"{k}: {recent.get(k)}")

fetch_and_print("VHC", "INCOME_STATEMENT")
fetch_and_print("FPT", "INCOME_STATEMENT")
