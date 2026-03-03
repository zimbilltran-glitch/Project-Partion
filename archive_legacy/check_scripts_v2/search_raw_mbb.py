import json
import os

def search_raw_mbb():
    base_dir = r'd:\Project_partial\Finsang\sub-projects\Version_2'
    files = ['_raw_mbb_balance_sheet.json', '_raw_mbb_income_statement.json', '_raw_mbb_note.json']
    
    terms = ["không kỳ hạn", "nợ xấu", "nợ nhóm", "quá hạn", "vốn chủ", "cho vay"]
    results = []
    
    for filename in files:
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path): continue
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.json_load(f) if hasattr(json, 'json_load') else json.load(f)
        
        # Vietcap raw JSON structure is usually a list of dicts in 'data' key or similar
        items = data.get('data', []) if isinstance(data, dict) else data
        
        for item in items:
            name = item.get('name', '').lower()
            name_en = item.get('nameEn', '').lower()
            for term in terms:
                if term in name or term in name_en:
                    results.append({
                        'file': filename,
                        'id': item.get('fieldId'),
                        'name': item.get('name'),
                        'name_en': item.get('nameEn')
                    })
    
    output_path = os.path.join(base_dir, 'mbb_search_results.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    search_raw_mbb()
