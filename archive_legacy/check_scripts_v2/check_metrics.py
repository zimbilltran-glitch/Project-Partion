import json

with open("sub-projects/Version_2/golden_schema.json", "r", encoding="utf-8") as f:
    fields = json.load(f)["fields"]

print("-- BANK --")
bank = {f["vietcap_key"]: f["field_id"] for f in fields if f["sheet"].endswith("_BANK")}
print("Tong ts:", bank.get("bsa53"))
print("Tien:", bank.get("bsa2"))
print("Cho vay KH:", bank.get("bsb132"))
print("Tong nv:", bank.get("bsb132")) # ? bsb132 is Tong nguon von or Cho vay?
print("Tien gui KH:", bank.get("bsb179")) # Wait, let's see what "bsb132" is
print("bsb132:", [f["vn_name"] for f in fields if f["vietcap_key"]=="bsb132"])

print("-- SEC --")
sec = {f["vietcap_key"]: f["field_id"] for f in fields if f["sheet"].endswith("_SEC")}
print("Tong ts:", sec.get("bsa53"))
print("Tien:", sec.get("bsa2"))
print("Vay ngan han:", sec.get("bsa55"))
print("FVTPL:", sec.get("bsa6"))
print("Tong nv:", sec.get("bsb132"))
