import requests
import json

urls = {
    "MBB": "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/MBB/financial-statement/metrics",
    "SSI": "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/SSI/financial-statement/metrics",
    "HPG": "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/HPG/financial-statement/metrics"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Origin": "https://trading.vietcap.com.vn",
    "Referer": "https://trading.vietcap.com.vn/"
}

for ticker, url in urls.items():
    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code == 200:
        with open(f".tmp/{ticker}_metrics.json", "w", encoding="utf-8") as f:
            json.dump(r.json(), f, ensure_ascii=False, indent=2)
        print(f"Dumped {ticker}")
    else:
        print(f"Failed {ticker}: {r.status_code}")
