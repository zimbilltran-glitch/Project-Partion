import requests, json

def get_tcbs(ticker):
    headers = {
        "Accept": "application/json",
        "DNT": "1",
        "Connection": "keep-alive"
    }
    
    # TCBS APIs
    urls = {
        "balance_sheet": f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/finance/{ticker}/balancesheet?yearly=1&isAll=false",
        "income_statement": f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/finance/{ticker}/incomestatement?yearly=1&isAll=false",
        "cash_flow": f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/finance/{ticker}/cashflow?yearly=1&isAll=false"
    }
    
    res = {}
    for name, url in urls.items():
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res[name] = r.json()
        else:
            print(f"Failed TCBS {name} for {ticker}: {r.status_code}")
    
    with open(f".tmp/tcbs_{ticker.lower()}.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f"Dumped TCBS for {ticker}")

get_tcbs("MBB")
get_tcbs("SSI")
