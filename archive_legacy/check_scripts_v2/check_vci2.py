import requests

for sec in ["BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW"]:
    url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/MBB/financial-statement?section={sec}"
    r = requests.get(url, timeout=20, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://trading.vietcap.com.vn/",
    })
    
    # Are there any other paths on Vietcap? Like meta?
    # No, it's just raw data. But how does Vietcap Web know what `bsa1` maps to?!
    # Usually they download a config or a localization file.
