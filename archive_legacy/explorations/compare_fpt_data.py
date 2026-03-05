"""
Compare Supabase data vs Vietcap raw API data for FPT Balance Sheet 2024.
Reads raw API JSON and golden_schema.json to identify misaligned keys.
"""
import json

BASE = r'd:\Project_partial\Finsang\sub-projects\Version_2'

# Load schema
with open(f'{BASE}\\golden_schema.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Load raw FPT 2024 data
with open(f'{BASE}\\_fpt_bs_2024.json', 'r', encoding='utf-8') as f:
    api_row = json.load(f)

# Get CDKT fields from schema (normal company, not bank/sec)
cdkt_fields = [f for f in schema['fields'] if f['sheet'] == 'CDKT']
cdkt_fields.sort(key=lambda x: x.get('row_number', 0))

results = []
for idx, field in enumerate(cdkt_fields[:50], start=1):
    field_id = field['field_id']
    vn_name = field['vn_name']
    vietcap_key = field.get('vietcap_key', '')
    
    # Get value using the mapped vietcap_key
    mapped_val = api_row.get(vietcap_key, 'N/A') if vietcap_key else 'NO_KEY'
    
    results.append({
        'row': idx,
        'field_id': field_id,
        'vn_name': vn_name,
        'vietcap_key': vietcap_key,
        'mapped_value': mapped_val,
    })

# Output to file
with open(f'{BASE}\\_fpt_comparison.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
