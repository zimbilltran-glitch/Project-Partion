import json
from pathlib import Path

SCHEMA_PATH = Path("c:/Users/Admin/OneDrive/Learn Anything/Antigravity/2.Project v2/sub-projects/Version_2/golden_schema.json")

def search_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    keywords = [
        "Tổng cộng tài sản",
        "Lợi nhuận sau thuế",
        "Vốn chủ sở hữu",
        "Lưu chuyển tiền thuần từ hoạt động kinh doanh",
        "Lưu chuyển tiền thuần từ hoạt động đầu tư",
        "Lưu chuyển tiền thuần từ hoạt động tài chính",
        "Lưu chuyển tiền thuần trong kỳ"
    ]
    
    print(f"Searching for keywords in {SCHEMA_PATH.name}...")
    for kw in keywords:
        print(f"\nResults for '{kw}':")
        found = False
        for f in schema["fields"]:
            if kw.lower() in f["vn_name"].lower():
                print(f"  - {f['field_id']:<60} | {f['sheet']:<10} | {f['vn_name']}")
                found = True
        if not found:
            print("  NO MATCH")

if __name__ == "__main__":
    search_schema()
