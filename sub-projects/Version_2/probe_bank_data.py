import requests, json
from pathlib import Path

OUT = Path(r'd:\Project_partial\Finsang\sub-projects\Version_2')
TICKER = "MBB"
SECTIONS = ["BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW", "NOTE"]
BASE = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{t}/financial-statement?section={s}"
RATIO_URL = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{t}/financial-ratio"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://trading.vietcap.com.vn/",
    "Origin": "https://trading.vietcap.com.vn",
}

def probe():
    # 1. Probe standard sections for MBB
    for sec in SECTIONS:
        url = BASE.format(t=TICKER, s=sec)
        print(f"  GET {sec} (MBB)...", end=" ")
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            data = r.json()
            out_f = OUT / f"_raw_mbb_{sec.lower()}.json"
            with open(out_f, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("200 OK")
        else:
            print(f"ERROR {r.status_code}")

    # 2. Probe for a potential ratio endpoint
    url = RATIO_URL.format(t=TICKER)
    print(f"  GET FINANCIAL_RATIO (MBB)...", end=" ")
    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code == 200:
        data = r.json()
        out_f = OUT / "_raw_mbb_ratio.json"
        with open(out_f, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("200 OK (Found ratio endpoint!)")
    else:
        print(f"ERROR {r.status_code} (Ratio endpoint likely doesn't exist at this URL)")

if __name__ == "__main__":
    probe()
