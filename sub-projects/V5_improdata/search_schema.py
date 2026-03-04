import json
from pathlib import Path

SCHEMA_F = Path(r"d:\Project_partial\Finsang\sub-projects\Version_2\golden_schema.json")

with open(SCHEMA_F, "r", encoding="utf-8") as f:
    data = json.load(f)

keyword = "kỳ hạn"
for field in data["fields"]:
    vn_name = field.get("vn_name", "").lower()
    if keyword in vn_name:
         # Only print ID to avoid Unicode
         print(f"ID: {field['field_id']} | Sheet: {field['sheet']}")
