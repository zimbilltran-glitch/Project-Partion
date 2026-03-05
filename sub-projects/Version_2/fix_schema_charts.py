import json

fixes_normal = {
    'cdkt_dau_tu_ngan_han': 'bsa3',
    'cdkt_cac_khoan_phai_thu': 'bsa5',
    'cdkt_hang_ton_kho': 'bsa15',
    'cdkt_tai_san_co_dinh': 'bsa23',
    'cdkt_tai_san_do_dang_dai_han': 'bsa34',
    'cdkt_phai_tra_nguoi_ban': 'bsa56',
    'cdkt_nguoi_mua_tra_tien_truoc': 'bsa57',
    'cdkt_vay_ngan_han': 'bsa60',
    'cdkt_vay_dai_han': 'bsa71',
    'cdkt_von_gop': 'bsa80',
    'cdkt_loi_nhuan_sau_thue_chua_phan_phoi': 'bsa90',
    'cdkt_co_phieu_quy': 'bsa83'
}

with open("lite_schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

for f in schema['fields']:
    if f['sheet'] == 'CDKT' and f['field_id'] in fixes_normal:
        # It's an object if we want multi-sector, but for 'CDKT' it's only Normal
        if f['vietcap_key'] is None:
            f['vietcap_key'] = {'normal': fixes_normal[f['field_id']]}
        elif isinstance(f['vietcap_key'], dict):
            f['vietcap_key']['normal'] = fixes_normal[f['field_id']]
        else:
            f['vietcap_key'] = {'normal': fixes_normal[f['field_id']]}

with open("lite_schema.json", "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)

print("Updated lite_schema.json with chart keys for Normal sector.")
