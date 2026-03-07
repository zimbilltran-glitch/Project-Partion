import os, sys, glob, math
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path='c:/Users/Admin/OneDrive/Learn Anything/Antigravity/2.Project v2/.env')
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
sb = create_client(url, key)

excel_files = glob.glob('data/excel_imports/*_BCTC_Vietcap.xlsx')

for file_path in excel_files:
    ticker = os.path.basename(file_path).split('_')[0]
    print(f"Processing NOTE sheet for {ticker}...")
    try:
        df = pd.read_excel(file_path, sheet_name='Note', skiprows=10, engine='openpyxl')
    except Exception as e:
        print(f"Skipping {ticker}, could not read Note sheet: {e}")
        continue
    
    rows = []
    # Identify period columns
    period_cols = {}
    for col in df.columns:
        if str(col).startswith('Unnamed'):
            continue
        col_str = str(col).strip()
        if col_str.isdigit():
            period_cols[col] = col_str
        elif col_str.startswith('Q') and ' 20' in col_str:
            # "Q1 2024" -> "Q1/2024"
            period_cols[col] = col_str.replace(' ', '/')

    # Process rows
    for row_idx, row in df.iterrows():
        item = str(row.iloc[0]).strip()
        if not item or item == 'nan':
            continue
        
        # Determine level based on indentation or capitalization
        # Since Excel might have spaces, let's use a very basic heuristic:
        # if item is ALL UPPER, level = 0, else 1
        level = 0 if item.isupper() else 1
        
        for p_col, p_name in period_cols.items():
            val = row[p_col]
            if pd.isna(val) or not isinstance(val, (int, float)) or not math.isfinite(val):
                continue
            
            rows.append({
                "stock_name": ticker,
                "asset_type": "STOCK",
                "source": "vietcap_excel",
                "item_id": f"note_{row_idx}",
                "item": item,
                "levels": level,
                "row_number": row_idx + 1,
                "period": p_name,
                "unit": "tỷ đồng",
                "value": float(val)
            })
            
    # Upsert in chunks
    if rows:
        print(f"  Pushing {len(rows)} rows to note table...")
        chunk_size = 1000
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i:i + chunk_size]
            try:
                res = sb.table('note').upsert(chunk, on_conflict="stock_name, item_id, period, source").execute()
            except Exception as e:
                print(f"  Upsert error at {ticker}: {e}")
        print(f"  {ticker} NOTE sync complete.")
    else:
        print(f"  No valid rows for {ticker}.")

print("DONE SYNCING NOTE SHEETS.")
