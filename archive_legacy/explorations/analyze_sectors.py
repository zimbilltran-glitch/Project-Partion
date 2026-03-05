import os
from dotenv import load_dotenv
import supabase
import pandas as pd

load_dotenv()
sb = supabase.create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Representative tickers for each sector in VN30
SECTORS = {
    "Bank": "MBB",         # Ngân hàng
    "Financial": "SSI",    # Chứng khoán / Dịch vụ tài chính
    "Non-Financial": "HPG" # Bất động sản / Sản xuất / Bán lẻ
}

def get_fields(ticker, table):
    try:
        # Get one recent period to see which fields exist
        res = sb.table(table).select("item_id, item").eq("stock_name", ticker).eq("period", "2024").execute()
        return {r["item_id"]: r["item"] for r in res.data}
    except Exception as e:
        print(f"Error fetching {ticker} from {table}: {e}")
        return {}

results = {}
for sector, ticker in SECTORS.items():
    cdkt = get_fields(ticker, "balance_sheet")
    kqkd = get_fields(ticker, "income_statement")
    results[sector] = {"cdkt": cdkt, "kqkd": kqkd}
    print(f"{sector} ({ticker}) -> CDKT: {len(cdkt)} items, KQKD: {len(kqkd)} items")

# Compare CDKT
bank_cdkt = set(results["Bank"]["cdkt"].keys())
fin_cdkt = set(results["Financial"]["cdkt"].keys())
nonfin_cdkt = set(results["Non-Financial"]["cdkt"].keys())

print("\n--- Balance Sheet (CDKT) Differences ---")
print(f"Common items across ALL 3 sectors: {len(bank_cdkt & fin_cdkt & nonfin_cdkt)}")
print("\nItems ONLY in Banks (MBB) [Sample of 5]:")
for item in list(bank_cdkt - fin_cdkt - nonfin_cdkt)[:5]:
    print(f"  - {results['Bank']['cdkt'][item]} ({item})")

print("\nItems ONLY in Non-Financial (HPG) [Sample of 5]:")
for item in list(nonfin_cdkt - bank_cdkt - fin_cdkt)[:5]:
    print(f"  - {results['Non-Financial']['cdkt'][item]} ({item})")

print("\nItems missing in Banks but exist in Non-Financial [Sample of 5]:")
for item in list(nonfin_cdkt - bank_cdkt)[:5]:
    print(f"  - {results['Non-Financial']['cdkt'][item]} ({item})")
