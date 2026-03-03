import requests
url = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/MBB/financial-statement?section=BALANCE_SHEET"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
data = r.json()
print("Top-level keys:", data.keys())

# Are there any other endpoints in Vietcap?
import time
urls = [
    "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/MBB/financial-statement-metadata",
    "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/MBB/financial-statement/meta",
    "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/MBB/financial-statement",
]
for u in urls:
    try:
        rr = requests.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        print(f"{u} => {rr.status_code}")
    except:
        pass
