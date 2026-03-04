import json

def find_in_json(filepath, target_val, year, prefix=""):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for period in data.get("data", {}).get("years", []):
        if period.get("yearReport") == year:
            for k, v in period.items():
                if k.startswith(prefix) and isinstance(v, (int, float)):
                    if abs(v - target_val) < 1000:
                        print(f"MATCH: {k} = {v}")
                        return k
            print(f"NOT FOUND: {target_val}")
            return None

print("VCI 2024:")
find_in_json("_raw_vci_is.json", 1778614820544, 2024, "iss") # FVTPL
find_in_json("_raw_vci_is.json", 1759391703072, 2024, "iss") # Lãi bán các ts FVTPL
find_in_json("_raw_vci_is.json", 729603724265, 2024, "iss") # Môi giới

print("\nMBB 2024:")
find_in_json("_raw_mbb_is.json", 41152219000000, 2024, "isb") # Thu nhập lãi thuần
find_in_json("_raw_mbb_is.json", 22951264000000, 2024, "isb") # Lợi nhuận sau thuế
