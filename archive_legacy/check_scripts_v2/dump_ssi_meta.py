import json

with open(".tmp/SSI_metrics.json", "r", encoding="utf-8") as f:
    sec_meta = json.load(f)["data"]

print("-- SEC BALANCE SHEET --")
for r in sec_meta["BALANCE_SHEET"]:
    if r["field"]:
        print(f"{r['field']} : {r['titleVi']}")

