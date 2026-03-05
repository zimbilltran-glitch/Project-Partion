import json
from pathlib import Path

SCHEMA_F = Path(r"d:\Project_partial\Finsang\sub-projects\Version_2\golden_schema.json")

with open(SCHEMA_F, "r", encoding="utf-8") as f:
    data = json.load(f)

sheets = sorted(list(set(f["sheet"] for f in data["fields"])))
print(f"Sheets found: {sheets}")
mask = [s for s in sheets if "BANK" in s]
print(f"Bank sheets: {mask}")
