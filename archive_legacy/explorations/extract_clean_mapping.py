import json
import os

def extract_clean_mapping():
    base_dir = r'd:\Project_partial\Finsang\sub-projects\Version_2'
    schema_path = os.path.join(base_dir, 'golden_schema.json')
    output_path = os.path.join(base_dir, 'field_mapping_clean.txt')
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for field in data['fields']:
            f.write(f"{field.get('sheet', 'N/A')} | {field.get('field_id', 'N/A')} | {field.get('vietcap_key', 'N/A')} | {field.get('vn_name', 'N/A')}\n")

if __name__ == "__main__":
    extract_clean_mapping()
