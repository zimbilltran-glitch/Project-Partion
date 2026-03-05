import json
import re
import unicodedata

def slugify(text: str) -> str:
    text = str(text).strip().lower()
    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace("đ", "d").replace("Đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s_]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    text = re.sub(r"_+", "_", text)
    return text[:55]

with open("sub-projects/Version_2/golden_schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

# Keep the original sheets
original_fields = [f for f in schema["fields"] if f["sheet"] in ("CDKT", "KQKD", "LCTT", "NOTE")]

def add_fields(ticker, suffix):
    with open(f".tmp/{ticker}_metrics.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    new_fields = []
    
    mapping = {
        "BALANCE_SHEET": f"CDKT_{suffix}",
        "INCOME_STATEMENT": f"KQKD_{suffix}",
        "CASH_FLOW": f"LCTT_{suffix}"
    }
    
    for section, sheet_id in mapping.items():
        rows = meta["data"][section]
        for row in rows:
            if not row["field"]: continue # skip empty lines like OFF_BALANCE_SHEET
            
            vietcap_key = row["field"]
            vn_name = row["titleVi"]
            slug = slugify(vn_name)
            base_id = f"{sheet_id.lower()}_{slug}"
            field_id = base_id
            
            # handle duplicates
            count = 1
            while any(f["field_id"] == field_id for f in new_fields):
                field_id = f"{base_id}_{count}"
                count += 1
            
            level = row["level"] - 1 # 1-based to 0-based
            if level < 0: level = 0
            
            new_fields.append({
                "field_id": field_id,
                "sheet": sheet_id,
                "sheet_en": section.replace("_", " ").title(),
                "sheet_vn": sheet_id.replace("_", " "),
                "vn_name": vn_name,
                "en_name": row["titleEn"] or "",
                "unit": "tỷ đồng",
                "data_type": "DECIMAL(22,2)",
                "level": level,
                "row_number": len(new_fields) + 1,
                "vietcap_key": vietcap_key,
                "vietcap_mapped": True,
                "notes": ""
            })
    return new_fields

bank_fields = add_fields("MBB", "BANK")
sec_fields = add_fields("SSI", "SEC")

schema["fields"] = original_fields + bank_fields + sec_fields
schema["total_fields"] = len(schema["fields"])

# Update sheet_counts
counts = {}
for code in ["CDKT", "KQKD", "LCTT", "NOTE", "CDKT_BANK", "KQKD_BANK", "LCTT_BANK", "CDKT_SEC", "KQKD_SEC", "LCTT_SEC"]:
    c = len([f for f in schema["fields"] if f["sheet"] == code])
    if c > 0: counts[code] = c
    
schema["sheet_counts"] = counts

# Also add them to period_columns to avoid KeyError
for code in ["CDKT_BANK", "KQKD_BANK", "LCTT_BANK", "CDKT_SEC", "KQKD_SEC", "LCTT_SEC"]:
    base = code.split("_")[0]
    schema["period_columns"][code] = schema["period_columns"][base]

with open("sub-projects/Version_2/golden_schema.json", "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)

print(f"Updated golden_schema.json with Bank and Sec forms. Total: {len(schema['fields'])}")
