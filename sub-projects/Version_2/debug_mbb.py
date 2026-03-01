import os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "sub-projects/Version_2")
from dotenv import load_dotenv
load_dotenv(".env")
from metrics import calc_metrics

df = calc_metrics("MBB", "year")
if df.empty:
    print("EMPTY DataFrame!")
else:
    print(f"Total rows: {len(df)}")
    for _, r in df.iterrows():
        vals_2024 = r.get("2024", None)
        vals_2023 = r.get("2023", None) 
        status = "OK" if (vals_2024 and vals_2024 != 0) else "ZERO"
        print(f"  [{status}] {r['item_id']:<10} | {r['vn_name']:<40} | 2024={vals_2024} | 2023={vals_2023}")
