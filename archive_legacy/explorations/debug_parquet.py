import pandas as pd
import io
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Version_2'))

from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data" / "financial"

def try_read(pq_path):
    """Try to read parquet, with or without encryption."""
    try:
        return pd.read_parquet(pq_path)
    except:
        pass
    try:
        from security import get_cipher
        cipher = get_cipher()
        if cipher:
            with open(pq_path, "rb") as f:
                decrypted = cipher.decrypt(f.read())
            return pd.read_parquet(io.BytesIO(decrypted))
    except:
        pass
    return None

ticker = "FPT"

# Check IS (income statement)
is_path = DATA_DIR / ticker / "period_type=year" / "sheet=kqkd" / f"{ticker}.parquet"
print(f"IS path exists: {is_path.exists()}")

is_df = try_read(is_path)
if is_df is not None:
    print(f"IS columns: {is_df.columns.tolist()}")
    fids = is_df["field_id"].unique().tolist()
    print(f"IS field_ids ({len(fids)}):")
    for fid in sorted(fids):
        print(f"  {fid}")
    
    # Check for net income field
    ni_fields = [f for f in fids if "loi_nhuan" in f.lower()]
    print(f"\nFields with 'loi_nhuan': {ni_fields}")
    
    # Check actual values for 2024
    for fid in ni_fields:
        row = is_df[(is_df["field_id"] == fid) & (is_df["period_label"] == "2024")]
        if len(row) > 0:
            print(f"  {fid} [2024] = {row.iloc[0]['value']}")
else:
    print("Failed to read IS parquet")

# Check BS
bs_path = DATA_DIR / ticker / "period_type=year" / "sheet=cdkt" / f"{ticker}.parquet"
print(f"\nBS path exists: {bs_path.exists()}")
bs_df = try_read(bs_path)
if bs_df is not None:
    fids = bs_df["field_id"].unique().tolist()
    eq_fields = [f for f in fids if "von_chu" in f.lower() or "tong_cong" in f.lower()]
    print(f"Fields with 'von_chu' or 'tong_cong': {eq_fields}")
    for fid in eq_fields:
        row = bs_df[(bs_df["field_id"] == fid) & (bs_df["period_label"] == "2024")]
        if len(row) > 0:
            print(f"  {fid} [2024] = {row.iloc[0]['value']}")
else:
    print("Failed to read BS parquet")
