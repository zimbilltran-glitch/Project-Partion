"""Phase L: Inspect raw JSON structure from Vietcap API responses."""
import json
from pathlib import Path

for fname in sorted(Path(__file__).parent.glob("_raw_*.json")):
    with open(fname, encoding="utf-8") as f:
        data = json.load(f)
    print(f"=== {fname.name} ===")
    print(f"  Top keys: {list(data.keys())}")
    if "data" in data:
        d = data["data"]
        print(f"  data type: {type(d).__name__}")
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, list) and len(v) > 0:
                    first = v[0]
                    fkeys = list(first.keys()) if isinstance(first, dict) else type(first).__name__
                    print(f"  data['{k}'] list[{len(v)}] -> item keys: {fkeys}")
                    # Print sample item
                    if isinstance(first, dict):
                        print(f"           sample: {json.dumps(first, ensure_ascii=False)[:300]}")
                else:
                    print(f"  data['{k}']: {str(v)[:80]}")
        elif isinstance(d, list) and len(d) > 0:
            print(f"  data list[{len(d)}], first keys: {list(d[0].keys()) if isinstance(d[0], dict) else 'n/a'}")
            print(f"  sample[0]: {json.dumps(d[0], ensure_ascii=False)[:300]}")
    print()
