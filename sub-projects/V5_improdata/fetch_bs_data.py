import requests
import json

def fetch_and_save(ticker, section, filepath):
    url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/financial-statement?section={section}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://trading.vietcap.com.vn/",
        "Origin": "https://trading.vietcap.com.vn",
    }
    r = requests.get(url, headers=headers)
    data = r.json()
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {ticker} {section} to {filepath}")

fetch_and_save("VCI", "BALANCE_SHEET", "_raw_vci_bs.json")
fetch_and_save("MBB", "BALANCE_SHEET", "_raw_mbb_bs.json")
fetch_and_save("FPT", "BALANCE_SHEET", "_raw_fpt_bs.json")
