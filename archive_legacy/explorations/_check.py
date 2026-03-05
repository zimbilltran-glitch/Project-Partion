import json

s = json.load(open(r'd:\Project_partial\Finsang\sub-projects\Version_2\golden_schema.json', 'r', encoding='utf-8'))
cdkt = [f for f in s['fields'] if f['sheet'] == 'CDKT']
cdkt.sort(key=lambda x: x.get('row_number', 0))

lines = []
for i, f in enumerate(cdkt):
    lines.append(f"{i:3d} | row={f['row_number']:3d} | key={f['vietcap_key']:10s} | {f['field_id']}")

with open(r'd:\Project_partial\Finsang\sub-projects\V5_improdata\_cdkt_mapping_check.txt', 'w', encoding='utf-8') as out:
    out.write('\n'.join(lines))
