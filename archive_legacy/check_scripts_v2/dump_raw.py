import os, json
from pipeline import VietcapProvider
from dotenv import load_dotenv

load_dotenv()
provider = VietcapProvider()

for ticker in ["MBB", "SSI"]:
    for section in ["BALANCE_SHEET", "INCOME_STATEMENT"]:
        data = provider.fetch_section(ticker, section)
        if data and "years" in data and len(data["years"]) > 0:
            # Sort by year descending, take latest 1
            latest = sorted(data["years"], key=lambda x: x.get("yearReport", 0), reverse=True)[0]
            with open(f".tmp/{ticker}_{section}.json", "w", encoding="utf-8") as f:
                json.dump(latest, f, ensure_ascii=False, indent=2)
            print(f"Dumped {ticker} {section}")
