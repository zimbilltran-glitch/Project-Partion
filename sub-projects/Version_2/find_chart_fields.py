import json

with open("lite_schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

# Need to check these names
targets = {
    'CDKT': [
        "tiền và", "đầu tư", "phải thu ngắn hạn", "hàng tồn kho",
        "tài sản cố định", "tài sản dở dang", "tài sản ngắn hạn khác",
        "vay ngắn hạn", "vay dài hạn", "phải trả người bán",
        "người mua trả tiền trước", "vốn góp", "lợi nhuận sau thuế chưa phân phối", "cổ phiếu quỹ"
    ],
    'CDKT_BANK': [
        "tiền mặt", "chứng khoán đầu tư", "tài sản cố định", "tài sản có khác",
        "tiền gửi của khách"
    ],
    'CDKT_SEC': [
        "fvt", "cho vay", "tiền và", "vay", "vốn chủ", "lợi nhuận"
    ]
}

with open("find_fields.txt", "w", encoding="utf-8") as out:
    for sheet, terms in targets.items():
        out.write(f"\n--- {sheet} ---\n")
        for field in schema['fields']:
            if field['sheet'] == sheet:
                lw = field['vn_name'].lower()
                for term in terms:
                    if term in lw:
                        out.write(f"{field['field_id']} | {field['vn_name']} | {field.get('vietcap_key')}\n")
                        break
