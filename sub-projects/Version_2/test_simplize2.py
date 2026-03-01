import requests, json

url = "https://api.simplize.vn/api/company/fi/statement/MBB?statementDate=2024-12-31&period=Y"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://simplize.vn",
    "Referer": "https://simplize.vn/"
}
r = requests.get(url, headers=headers)
print(r.status_code)
if r.status_code == 200:
    print(r.json()[:2])
