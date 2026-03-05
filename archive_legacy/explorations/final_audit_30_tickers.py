import os
import supabase
from dotenv import load_dotenv

load_dotenv()
sb = supabase.create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

TICKERS = ["ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG", 
           "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB", 
           "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE"]

TABLES = ["balance_sheet", "income_statement", "cash_flow", "financial_ratios"]

def audit():
    print(f"{'Ticker':<10} | {'BS':<6} | {'IS':<6} | {'CF':<6} | {'CSTC':<6}")
    print("-" * 50)
    for ticker in TICKERS:
        counts = []
        for table in TABLES:
            try:
                # Use count='exact' to avoid pagination limits in the count
                res = sb.table(table).select("id", count="exact").eq("stock_name", ticker).execute()
                counts.append(res.count if res.count is not None else 0)
            except Exception:
                counts.append("ERR")
        print(f"{ticker:<10} | {counts[0]:<6} | {counts[1]:<6} | {counts[2]:<6} | {counts[3]:<6}")

if __name__ == "__main__":
    audit()
