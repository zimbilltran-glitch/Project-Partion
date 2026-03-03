import json

with open("sub-projects/Version_2/golden_schema.json", "r", encoding="utf-8") as f:
    fields = json.load(f)["fields"]

bank = {f["vietcap_key"]: f["field_id"] for f in fields if f["sheet"].endswith("_BANK")}
sec = {f["vietcap_key"]: f["field_id"] for f in fields if f["sheet"].endswith("_SEC")}

print("\n--- BANK METRICS ---")
print("TCT: bsa53 ->", bank.get("bsa53"))
print("Cho vay KH: bsb132 ->", bank.get("bsb132")) # Wait bsb103 is cho vay KH! Let me check JSON!
print("bsb103:", bank.get("bsb103"))
print("Tien gui KH: bsb113 ->", bank.get("bsb113"))
print("NII (Thu nhap lai thuan): isb27 ->", bank.get("isb27"))
print("LNTT: isa20 ->", bank.get("isa20"))
print("LNST: isa22 ->", bank.get("isa22"))
print("Von CSH: bsa78 ->", bank.get("bsa78"))

print("\n--- SEC METRICS ---")
print("TCTS: bsa53 ->", sec.get("bsa53"))
print("FVTPL: bsa6 ->", sec.get("bsa6"))
print("HTM: bsa12 ->", sec.get("bsa12"))
print("Cho vay margin: bsa15 ->", sec.get("bsa15"))
print("No vay ngan han: bsa55 ->", sec.get("bsa55"))
print("No vay dai han: bsa67 ->", sec.get("bsa67"))
print("Von CSH: bsa78 ->", sec.get("bsa78"))
print("Doanh thu HDB: isa3 ->", sec.get("isa3")) # might be isa5_1? Let's print isa5_1
print("Doanh thu FVTPL: isa5_1 ->", sec.get("isa5_1")) 
print("Doanh thu moi gioi: isa5_8 ->", sec.get("isa5_8"))
print("LNTT: isa20 ->", sec.get("isa20"))
print("LNST: isa22 ->", sec.get("isa22"))
