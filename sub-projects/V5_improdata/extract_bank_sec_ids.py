import json

schema_path = "c:/Users/Admin/OneDrive/Learn Anything/Antigravity/2.Project v2/sub-projects/Version_2/golden_schema.json"
with open(schema_path, "r", encoding="utf-8") as f:
    schema = json.load(f)

# Targets for Banks
bank_targets = {
    "CDKT_BANK": ["tổng tài sản", "tiền mặt", "cho vay khách hàng", "tiền gửi của khách hàng", "vốn chủ sở hữu", "lợi ích của cổ đông thiểu số"],
    "KQKD_BANK": ["thu nhập lãi thuần", "lợi nhuận thuần từ hdkd", "tổng lợi nhuận kế toán trước thuế", "lợi nhuận sau thuế", "cổ đông của công ty mẹ"]
}

# Targets for Securities
sec_targets = {
    "CDKT_SEC": ["tổng tài sản", "cho vay", "vốn chủ sở hữu"],
    "KQKD_SEC": ["doanh thu môi giới", "lợi nhuận kế toán trước thuế", "lợi nhuận sau thuế", "công ty mẹ"]
}

results = {}

for sheet, keywords in {**bank_targets, **sec_targets}.items():
    print(f"\n--- {sheet} ---")
    results[sheet] = []
    for f in schema["fields"]:
        if f["sheet"] == sheet:
            name = f["vn_name"].lower()
            if any(k in name for k in keywords):
                print(f"{f['field_id']:<45}: {f['vn_name']}")
                results[sheet].append({"id": f["field_id"], "name": f["vn_name"]})

with open("_bank_sec_extracted.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
