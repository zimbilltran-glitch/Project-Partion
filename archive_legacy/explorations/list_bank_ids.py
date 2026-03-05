import json
from pathlib import Path

SCHEMA_F = Path(r"d:\Project_partial\Finsang\sub-projects\Version_2\golden_schema.json")

with open(SCHEMA_F, "r", encoding="utf-8") as f:
    data = json.load(f)

for field in data["fields"]:
    if field["sheet"] == "CDKT_BANK":
         print(f"{field['field_id']}")
