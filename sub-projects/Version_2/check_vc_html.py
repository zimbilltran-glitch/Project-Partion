import requests

# Let's hit the actual financial-statement endpoint for SSI
url = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/SSI/financial-statement?section=BALANCE_SHEET"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Referer":"https://trading.vietcap.com.vn/", "Origin": "https://trading.vietcap.com.vn"})
if r.status_code == 200:
    data = r.json()
    keys = list(data.get("data", {}).get("years", [{}])[0].keys())
    print("SSI keys:", len(keys), keys[:20])

# Wait, we know `bsa1`, `bsa2` ... `bsa132`. How do we get the labels?
url = "https://trading.vietcap.com.vn/quote/SSI"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
print("Trading vietcap size:", len(r.text))
with open(".tmp/trading_ssi.html", "w", encoding="utf-8") as f:
    f.write(r.text)
