"""
Phase L — Link: Live Vietcap API Probe
Fires one GET per section, saves raw JSON to Version_2/_raw_*.json
No auth required — API is fully public.
"""
import requests, json
from pathlib import Path

OUT    = Path(__file__).parent
TICKER = "VHC"
SECTIONS = ["BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW", "NOTE"]
BASE   = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{t}/financial-statement?section={s}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://trading.vietcap.com.vn/",
    "Origin": "https://trading.vietcap.com.vn",
}

results = {}
for sec in SECTIONS:
    url = BASE.format(t=TICKER, s=sec)
    print(f"  GET {sec}...", end=" ", flush=True)
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            data = r.json()
            # Save raw JSON
            out_f = OUT / f"_raw_{sec.lower()}.json"
            with open(out_f, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            top_keys = list(data.keys())[:10] if isinstance(data, dict) else type(data).__name__
            results[sec] = {"status": 200, "top_keys": top_keys, "saved": out_f.name}
            print(f"200 OK | top keys: {top_keys}")
        else:
            results[sec] = {"status": r.status_code, "error": r.text[:300]}
            print(f"ERROR {r.status_code}: {r.text[:100]}")
    except Exception as e:
        results[sec] = {"error": str(e)}
        print(f"EXCEPTION: {e}")

print()
print("=== SUMMARY ===")
for sec, v in results.items():
    status = v.get("status", "ERR")
    print(f"  {sec}: {status}")
