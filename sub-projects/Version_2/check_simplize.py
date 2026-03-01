import requests, json

url = "https://api.simplize.vn/api/company/fi/statement/MBB?statementDate=2024-12-31&period=Y"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
if r.status_code == 200:
    data = r.json()
    with open(".tmp/simplize_mbb.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Simplize MBB dumped")

url = "https://api.simplize.vn/api/company/fi/statement/SSI?statementDate=2024-12-31&period=Y"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
if r.status_code == 200:
    data = r.json()
    with open(".tmp/simplize_ssi.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Simplize SSI dumped")
