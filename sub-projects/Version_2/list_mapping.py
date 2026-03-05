import json

with open("c:/Users/Admin/OneDrive/Learn Anything/Antigravity/2.Project v2/sub-projects/Version_2/lite_schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

with open("mapping_out.txt", "w", encoding="utf-8") as out:
    for sheet in ['CDKT', 'CDKT_BANK', 'CDKT_SEC']:
        out.write(f"\n--- {sheet} ---\n")
        for field in schema['fields']:
            if field['sheet'] == sheet and field['vietcap_key'] is not None:
                out.write(f"{field['field_id']}: {field['vn_name']} ({field['vietcap_key']})\n")
