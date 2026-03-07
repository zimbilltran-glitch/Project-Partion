import json, math, os, sys
import pandas as pd
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")
ROOT = Path(__file__).parent.parent.parent

def run_fix_for_ticker(ticker, sheet_name, sector, schema_sheet_id):
    # Load Schema
    schema_path = ROOT / "sub-projects" / "V2_Data_Pipeline" / "golden_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Scrape or use existing API data (we will fetch it directly using requests)
    import requests
    url = f"https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/financial-statement?section=BALANCE_SHEET"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    d = r.json()
    
    api_values = {}
    if d.get("successful") and d.get("data"):
        for row in d["data"]["years"]:
            if str(row["yearReport"]) == "2024":
                for k, v in row.items():
                    if isinstance(v, (int, float)):
                        api_values[k] = v

    # Load Excel Data
    excel_path = ROOT / "data" / "excel_imports" / f"{ticker}_BCTC_Vietcap.xlsx"
    df = pd.read_excel(excel_path, sheet_name=sheet_name, skiprows=10)
    col_2024 = [c for c in df.columns if str(c) == "2024"][0]

    # Map name -> value
    excel_map = {}
    for i, row in df.iterrows():
        name = str(row.iloc[0]).strip().lower()
        if name == "nan": continue
        val = row[col_2024]
        if pd.isna(val) or abs(val) < 1.0:
            continue
        excel_map[name] = val

    # Update Schema
    updates = 0
    for fld in schema["fields"]:
        if fld["sheet"] == schema_sheet_id:
            name_clean = fld["vn_name"].strip().lower()
            ex_val = None
            
            # Semantic search in excel map
            if name_clean in excel_map:
                ex_val = excel_map[name_clean]
            else:
                for k, v in excel_map.items():
                    if name_clean in k or k in name_clean:
                        ex_val = v
                        break
                        
            if ex_val is not None:
                matches = [ak for ak, av in api_values.items() if abs(av - ex_val) < 1.0 or abs(av - (ex_val * 1e9)) < 1.0]
                
                # filter matching by section (bsa/bsb/bss)
                # prefer bsb/bss over bsa if both match for bank/sec, otherwise prefer bsa
                if len(matches) > 1:
                    specific = [m for m in matches if m.startswith(f"bs{sector[0]}")]
                    if specific:
                        matches = specific
                
                if matches:
                    best_match = matches[0]
                    # update schema
                    if "vietcap_key" not in fld:
                        fld["vietcap_key"] = {}
                    if fld["vietcap_key"].get(sector) != best_match:
                        print(f"[{ticker}] Fix: {fld['vn_name']} -> {best_match} (was {fld['vietcap_key'].get(sector)})")
                        fld["vietcap_key"][sector] = best_match
                        updates += 1

    if updates > 0:
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        print(f"[{ticker}] Updated {updates} keys in schema.")
    else:
        print(f"[{ticker}] No updates needed.")

if __name__ == "__main__":
    run_fix_for_ticker("MBB", "Balance Sheet", "bank", "CDKT_BANK")
