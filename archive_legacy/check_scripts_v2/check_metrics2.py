import json

with open("sub-projects/Version_2/golden_schema.json", "r", encoding="utf-8") as f:
    fields = json.load(f)["fields"]

print("-- BANK --")
bank_fields = [f for f in fields if f["sheet"].endswith("_BANK")]
for f in bank_fields:
    print(f.get("vietcap_key"), f["field_id"], f["vn_name"])

print("-- SEC --")
sec_fields = [f for f in fields if f["sheet"].endswith("_SEC")]
for f in sec_fields:
    if f.get("vietcap_key") in ["bsa53", "bsa6", "isa5_1", "isa5_8", "isa22"]:
        print(f.get("vietcap_key"), f["field_id"], f["vn_name"])

