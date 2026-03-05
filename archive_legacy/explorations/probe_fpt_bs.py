"""
Probe Vietcap API for FPT Balance Sheet and save raw JSON for comparison.
"""
import requests, json
from pathlib import Path

OUT = Path(r'd:\Project_partial\Finsang\sub-projects\Version_2')
TICKER = "FPT"
SECTION = "BALANCE_SHEET"
BASE = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{t}/financial-statement?section={s}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://trading.vietcap.com.vn/",
    "Origin": "https://trading.vietcap.com.vn",
}

url = BASE.format(t=TICKER, s=SECTION)
r = requests.get(url, headers=HEADERS, timeout=20)
if r.status_code == 200:
    data = r.json()
    out_f = OUT / f"_raw_fpt_bs.json"
    with open(out_f, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Extract 2024 annual data (lengthReport=5)
    years = data.get('data', {}).get('years', [])
    for row in years:
        if row.get('yearReport') == 2024 and row.get('lengthReport') == 5:
            # Save just this year's data for easy comparison
            out_f2 = OUT / f"_fpt_bs_2024.json"
            with open(out_f2, "w", encoding="utf-8") as f:
                json.dump(row, f, ensure_ascii=False, indent=2)
            break
