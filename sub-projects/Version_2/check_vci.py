import requests

ticker = "MBB"
url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/financial-statement?section=BALANCE_SHEET"
r = requests.get(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://trading.vietcap.com.vn/",
    "Origin": "https://trading.vietcap.com.vn",
})
print("MBB data keys:", list(r.json().get("data", {}).keys()))
