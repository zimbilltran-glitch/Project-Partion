import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

headers = {
    'Accept': 'application/json, text/plain, */*',
    'x-client-source': 'MOBILE',
    'x-user-agent': 'vndirect-mobile-app', 
    'User-Agent': 'VNDIRECT/10.0.0 (iPhone; iOS 16.5; Scale/3.00)'
}

def fetch_raw_vndirect(ticker, report_type):
    # Mapping report types to VNDirect API codes
    type_map = {
        'cdkt': 1, # Balance Sheet
        'kqkd': 2, # Income Statement
        'lctt': 3  # Cash Flow
    }
    
    url = f"https://finfo-api.vndirect.com.vn/v4/financial_statements?q=code:{ticker}~reportType:QUARTER~modelType:{type_map[report_type]}&sort=-fiscalDate&size=100"
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json().get('data', [])
        
        # Extract unique item codes
        if not data:
            return {}
            
        items = {}
        for row in data:
            item_code = row.get('itemCode')
            item_name = row.get('itemName')
            if item_code and item_name:
                items[item_code] = item_name
        return items
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return {}

tickers = ["MBB", "SSI", "HPG"]
for ticker in tickers:
    items = fetch_raw_vndirect(ticker, 'cdkt')
    print(f"\n--- {ticker} Raw Balance Sheet Items ({len(items)}) ---")
    for k, v in list(items.items())[:10]:
        print(f"  {k}: {v}")
