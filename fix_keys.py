import json, os, sys
import pandas as pd
from pathlib import Path

ROOT = Path('c:/Users/Admin/OneDrive/Learn Anything/Antigravity/2.Project v2')

def run_fix_for_ticker(ticker, sheet_name, sector, schema_sheet_id, intercept_file):
    schema_path = ROOT / 'sub-projects' / 'V2_Data_Pipeline' / 'golden_schema.json'
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    # Load API payload from intercept
    with open(intercept_file, 'r', encoding='utf-8') as f:
        d = json.load(f)
        
    api_values = {}
    for url, val in d.items():
        if 'BALANCE_SHEET' in url and val['successful']:
            for row in val['data']['years']:
                if str(row['yearReport']) == '2024':
                    for k, v in row.items():
                        if isinstance(v, (int, float)):
                            api_values[k] = v

    # Load Excel reference
    excel_path = ROOT / 'data/excel_imports' / f'{ticker}_BCTC_Vietcap.xlsx'
    df = pd.read_excel(excel_path, sheet_name=sheet_name, skiprows=10)
    col_2024 = [c for c in df.columns if str(c) == '2024'][0]

    excel_map = {}
    for i, row in df.iterrows():
        name = str(row.iloc[0]).strip().lower()
        if name == 'nan': continue
        val = row[col_2024]
        if pd.isna(val) or abs(val) < 1.0:
            continue
        excel_map[name] = val

    updates = 0
    for fld in schema['fields']:
        if fld['sheet'] == schema_sheet_id:
            name_clean = fld['vn_name'].strip().lower()
            ex_val = None
            if name_clean in excel_map:
                ex_val = excel_map[name_clean]
                        
            if ex_val is not None:
                matches = [ak for ak, av in api_values.items() if abs(av - ex_val) < 1.0 or abs(av - (ex_val * 1e9)) < 1.0]

                if matches:
                    best_match = matches[0]
                    # Specificity
                    specific = [m for m in matches if m.startswith('bs' + sector[0])]
                    if len(specific) == 1:
                        best_match = specific[0]
                    elif len(matches) > 1 and len(specific) == 0:
                        best_match = matches[0]

                    if 'vietcap_key' not in fld or fld['vietcap_key'] is None:
                        fld['vietcap_key'] = {}
                    old_key = fld['vietcap_key'].get(sector, None)
                    if old_key != best_match:
                        print(f"[{ticker}] Fix: '{fld['vn_name']}' -> {best_match} (was {old_key})")
                        fld['vietcap_key'][sector] = best_match
                        updates += 1

    if updates > 0:
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        print(f"[{ticker}] Updated {updates} keys in schema.")

run_fix_for_ticker('MBB', 'Balance Sheet', 'bank', 'CDKT_BANK', 'mbb_intercepted.json')
