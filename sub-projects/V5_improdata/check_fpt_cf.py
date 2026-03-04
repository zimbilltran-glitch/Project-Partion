import requests, json
url = 'https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/FPT/financial-statement?section=CASH_FLOW'
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://trading.vietcap.com.vn/',
    'Origin': 'https://trading.vietcap.com.vn'
}
data = requests.get(url, headers=headers).json()
for p in data['data']['years']:
    if p['yearReport'] == 2023:
        for k in ['cfa20', 'cfa30', 'cfa40', 'cfa50']:
            print(f"FPT 2023 {k}: {p.get(k)}")
