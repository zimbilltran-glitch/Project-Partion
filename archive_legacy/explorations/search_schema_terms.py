import json
import os

def search_terms():
    base_dir = r'd:\Project_partial\Finsang\sub-projects\Version_2'
    schema_path = os.path.join(base_dir, 'golden_schema.json')
    output_path = os.path.join(base_dir, 'search_results.json')
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    terms = ["không kỳ hạn", "nợ xấu", "nợ nhóm", "quá hạn", "chi phí hoạt động", "môi giới"]
    results = {term: [] for term in terms}
    
    for field in data['fields']:
        vn_name = field.get('vn_name', '').lower()
        for term in terms:
            if term in vn_name:
                results[term].append({
                    'id': field['field_id'],
                    'name': field['vn_name'],
                    'sheet': field['sheet']
                })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    search_terms()
