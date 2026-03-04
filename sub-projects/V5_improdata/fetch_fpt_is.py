import requests, json, sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/FPT/financial-statement?section=INCOME_STATEMENT"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Referer": "https://trading.vietcap.com.vn/",
    "Origin": "https://trading.vietcap.com.vn",
}
r = requests.get(url, headers=headers)
data = r.json()
print("Success:", data.get("successful"))
if "data" in data and isinstance(data["data"], list):
    rows = data["data"]
    print("Rows count:", len(rows))
    for i, row in enumerate(rows):
        print(f"Row {i:02}: {row.get('key')} - {row.get('name')}")
