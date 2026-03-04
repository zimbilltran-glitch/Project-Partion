import json

with open("golden_schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

print("--- Securities (iss) ---")
for f in schema['fields']:
    if f['sheet'] == 'KQKD' and str(f.get('vietcap_key')).startswith('iss'):
        print(f"{f['id']:<45} : {f.get('vietcap_key')}")

print("\n--- Bank (isb) ---")
for f in schema['fields']:
    if f['sheet'] == 'KQKD' and str(f.get('vietcap_key')).startswith('isb'):
        print(f"{f['id']:<45} : {f.get('vietcap_key')}")

