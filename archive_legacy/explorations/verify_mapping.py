import pandas as pd
from pathlib import Path
import pyarrow.parquet as pq
import io
import sys
import os

# Ensure we can import from the current dir
sys.path.insert(0, os.getcwd())
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")
from security import get_cipher

def check_val(ticker, period, fid):
    path = Path('c:/Users/Admin/OneDrive/Learn Anything/Antigravity/2.Project v2/data/financial') / ticker.upper() / 'period_type=year' / 'sheet=kqkd' / f'{ticker.upper()}.parquet'
    if not path.exists():
        print(f"Path not found: {path}")
        return
    
    with open(path, 'rb') as f:
        data = f.read()
    
    cipher = get_cipher()
    if cipher:
        try:
            decrypted = cipher.decrypt(data)
            df = pd.read_parquet(io.BytesIO(decrypted))
            print(f"Read {ticker} (Encrypted)")
        except Exception as e:
            # Maybe it wasn't encrypted?
            try:
                df = pd.read_parquet(io.BytesIO(data))
                print(f"Read {ticker} (Raw - Decryption failed: {e})")
            except Exception as e2:
                print(f"Failed to read {ticker}: {e2}")
                return
    else:
        df = pd.read_parquet(io.BytesIO(data))
        print(f"Read {ticker} (Raw)")

    # Find the row
    row = df[(df['period_label'] == period) & (df['field_id'] == fid)]
    if not row.empty:
        print(f"  {ticker} {period} {fid}: {row.iloc[0]['value']:,} ({row.iloc[0]['vn_name']})")
    else:
        print(f"  {ticker} {period} {fid}: NOT FOUND")
        count = len(df[df['vietcap_mapped'] == True])
        print(f"  Total mapped fields: {count}")

print("--- VERIFICATION ---")
check_val('FPT', '2024', 'kqkd_loi_nhuan_cua_co_dong_cua_cong_ty_me')
check_val('MBB', '2024', 'kqkd_bank_thu_nhap_lai_thuan')
check_val('VCI', '2024', 'kqkd_doanh_thu_thuan')
