import os
from dotenv import load_dotenv
import supabase

load_dotenv()
sb = supabase.create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def verify_ticker(ticker):
    print(f"\n--- Verification for {ticker} ---")
    data = sb.table("financial_ratios_wide").select("*").eq("stock_name", ticker).order("row_number").limit(15).execute().data
    if not data:
        print("❌ No data found!")
        return
        
    for r in data:
        print(f"Row {r['row_number']:>2}: {r['item_id']:<10} | {r['item']:<35} | Level {r['levels']} | Unit {r['unit']}")

if __name__ == "__main__":
    verify_ticker("ACB")
    verify_ticker("FPT")
    verify_ticker("VIC")
