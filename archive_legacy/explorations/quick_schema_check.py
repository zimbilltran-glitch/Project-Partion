import json
from pathlib import Path

SCHEMA_PATH = Path("c:/Users/Admin/OneDrive/Learn Anything/Antigravity/2.Project v2/sub-projects/Version_2/golden_schema.json")

def quick_check():
    if not SCHEMA_PATH.exists():
        print(f"Error: Schema not found at {SCHEMA_PATH}")
        return

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Statistics
    total_fields = len(schema["fields"])
    mapped_fields = [f for f in schema["fields"] if f.get("vietcap_key") is not None]
    
    print(f"--- Schema Stats ---")
    print(f"Total fields: {total_fields}")
    print(f"Mapped fields: {len(mapped_fields)}")
    print(f"Coverage: {(len(mapped_fields)/total_fields)*100:.1f}%")

    # Group by sheet
    sheets = {}
    for f in mapped_fields:
        s = f["sheet"]
        sheets[s] = sheets.get(s, 0) + 1
    
    print(f"\nMapped fields by sheet:")
    for s, count in sorted(sheets.items()):
        print(f"  {s:<10}: {count}")

    # Specific check for core metrics
    core_ids = [
        "kqkd_doanh_thu_thuan",
        "kqkd_lai_thuan_sau_thue",
        "cdkt_tong_cong_tai_san",
        "cdkt_tong_von_chu_so_huu",
        "lctt_luu_chuyen_tien_thuan_trong_ky"
    ]
    
    print(f"\n--- Core Metric Check ---")
    for cid in core_ids:
        found = next((f for f in schema["fields"] if cid in f["field_id"]), None)
        if found:
            print(f"  {found['field_id']:<40}: {found['vietcap_key']}")
        else:
            print(f"  {cid:<40}: NOT FOUND")

if __name__ == "__main__":
    quick_check()
