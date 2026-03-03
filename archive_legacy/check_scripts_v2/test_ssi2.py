import requests
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "X-Fiin-Key": "CW-F1"
}
urls = [
    "https://fiin-fundamental.ssi.com.vn/FinancialStatement/GetIncomeStatement?language=vi&SecCode=MBB",
    "https://fiin-fundamental.ssi.com.vn/FinancialStatement/GetBalanceSheet?language=vi&SecCode=MBB",
    "https://fiin-fundamental.ssi.com.vn/FinancialStatement/GetCashFlow?language=vi&SecCode=MBB"
]
for u in urls:
    r = requests.get(u, headers=headers, timeout=20)
    print(r.status_code, len(r.text))
