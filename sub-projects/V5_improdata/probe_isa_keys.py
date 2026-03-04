"""
probe_isa_v2.py - Đọc raw IS JSON cẩn thận hơn để thấy mapping isa21-25
"""
import json, sys

sys.stdout.reconfigure(encoding='utf-8')

with open("_raw/FPT_INCOME_STATEMENT.json", encoding="utf-8") as f:
    data = json.load(f)

# data = {"years": [...], "quarters": [...]}
years_data = data.get("years", [])

print(f"Total years: {len(years_data)}")
if not years_data:
    print("No years data!")
    sys.exit()

# Look at most recent year (likely 2024 or first item)
# Sort by year desc
years_sorted = sorted(years_data, key=lambda x: x.get("year", 0) or x.get("createDate", ""), reverse=True)
recent = years_sorted[0]

print(f"\n=== Most recent year item ===")
print(f"Year: {recent.get('year') or recent.get('createDate')}")
print(f"Keys in record: {list(recent.keys())}")

print("\n=== All isa keys in most recent year ===")
for k, v in sorted(recent.items(), key=lambda x: (len(x[0]), x[0])):
    if k.startswith("isa"):
        num = int(k.replace("isa",""))
        print(f"  {k:<8}: {v}")
        if num > 27:
            break  # stop after a few extra

# Find the specific rows for isa18-isa25
print("\n=== isa18 through isa25 ===")
for n in range(18, 26):
    k = f"isa{n}"
    v = recent.get(k)
    print(f"  {k}: {v}")
