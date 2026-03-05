import json
import os

def extract_fields():
    # Use absolute path for golden_schema.json
    base_dir = r'd:\Project_partial\Finsang\sub-projects\Version_2'
    schema_path = os.path.join(base_dir, 'golden_schema.json')
    output_path = os.path.join(base_dir, 'sector_fields.json')
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sectors = ['CDKT_BANK', 'KQKD_BANK', 'CDKT_SEC', 'KQKD_SEC']
    result = {}
    
    for sector in sectors:
        result[sector] = []
        for field in data['fields']:
            if field['sheet'] == sector:
                result[sector].append({
                    'id': field['field_id'],
                    'name': field['vn_name']
                })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    extract_fields()
