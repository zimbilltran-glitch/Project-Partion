"""Find the year/quarter encoding in the quarters array."""
import json, warnings
warnings.filterwarnings("ignore")
from pathlib import Path

data = json.loads(Path("Version_2/_raw_balance_sheet.json").read_text(encoding="utf-8"))["data"]
quarters = data.get("quarters", [])
print(f"Total quarters: {len(quarters)}")
for i, q in enumerate(quarters[:5]):
    yr = q.get("yearReport")
    lr = q.get("lengthReport")  # This might be the quarter label number
    qr = q.get("quarterReport")
    # Find all non-null, non-standard meta fields
    meta = {k: v for k, v in q.items() if not k.startswith(("bsa","bsb","bss","bsi","nos","noa","cfa")) and v is not None}
    print(f"  [{i}] meta: {meta}")
