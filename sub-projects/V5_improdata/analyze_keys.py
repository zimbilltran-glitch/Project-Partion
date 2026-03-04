import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

def print_keys(filepath, ticker, section):
    print(f"\n--- {ticker} {section} ---")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for i, item in enumerate(data.get('data', [])):
            if item.get('key'):
                print(f"{i:03d} - {item['key']}: {item['name']}")

print_keys("_raw_vci_is.json", "VCI", "IS")
print_keys("_raw_mbb_is.json", "MBB", "IS")
print_keys("_raw_mbb_cf.json", "MBB", "CF")
