import requests, json
url = 'https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/FPT/financial-statement?section=INCOME_STATEMENT'
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://trading.vietcap.com.vn/',
    'Origin': 'https://trading.vietcap.com.vn'
}
data = requests.get(url, headers=headers).json()
for p in data['data']['years']:
    if p['yearReport'] == 2023:
        print(f"FPT 2023 isa22 (Profit for Parent): {p.get('isa22')}")
        print(f"FPT 2023 isa20 (Net Profit/PAT): {p.get('isa20')}")
    if p['yearReport'] == 2024:
        print(f"FPT 2024 isa22 (Profit for Parent): {p.get('isa22')}")
        print(f"FPT 2024 isa20 (Net Profit/PAT): {p.get('isa20')}")
