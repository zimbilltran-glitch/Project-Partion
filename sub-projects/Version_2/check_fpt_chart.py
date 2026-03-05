import json

d = json.load(open('probe_FPT_BS.json', encoding='utf-8'))
q = d['quarters'][0]
schema = json.load(open('lite_schema.json', encoding='utf-8'))

print("\n--- NORMAL (FPT) ---")
targets = [
    'Đầu tư ngắn hạn', 'Các khoản phải thu', 'Hàng tồn kho', 'Tài sản cố định',
    'Tài sản dở dang dài hạn', 'Tài sản ngắn hạn khác', 'Vay ngắn hạn', 'Vay dài hạn',
    'Phải trả người bán', 'Người mua trả tiền trước', 'Vốn góp', 'Lợi nhuận sau thuế chưa phân phối', 'Cổ phiếu quỹ'
]
for field in schema['fields']:
    if field['sheet'] == 'CDKT' and field['vn_name'] in targets:
         print(f"{field['field_id']} | {field['vn_name']} | {field['vietcap_key']}")
