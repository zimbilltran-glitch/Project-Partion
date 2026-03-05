"""
T1.1 — Tạo lite_schema.json
Chỉ giữ các fields cần thiết cho pipeline runtime:
  - field_id, sheet, vietcap_key (dict: normal/bank/sec → api key)
  - vietcap_mapped (bool flag), vn_name (semantic fallback), row_number (anchor index)
Loại bỏ: sample_values, notes, en_name, unit, data_type, level, sheet_en, sheet_vn...
"""
import json
import os

INPUT_PATH  = "sub-projects/Version_2/golden_schema.json"
OUTPUT_PATH = "sub-projects/Version_2/lite_schema.json"

# Keys giữ lại cho runtime pipeline
KEEP_FIELD_KEYS = {
    "field_id",       # primary key
    "sheet",          # CDKT / KQKD / LCTT / CDKT_BANK / ...
    "vietcap_key",    # dict {normal/bank/sec -> api_key} hoặc null
    "vietcap_mapped", # bool — True nếu field đã được map (có data)
    "vn_name",        # tên Tiếng Việt — dùng cho normalize() và UI display
    "row_number",     # anchor index dùng pipeline verify & tab ordering
    "unit",           # đơn vị (tỷ đồng, %) — cần cho build_rows_for_sheet()
    "level",          # indent level — cần cho UI hierarchy display
}

def build_lite_schema():
    with open(INPUT_PATH, encoding="utf-8") as f:
        full = json.load(f)

    lite_fields = []
    stats = {"total": 0, "mapped": 0, "unmapped": 0, "sheets": {}}

    for field in full["fields"]:
        lite = {k: field.get(k) for k in KEEP_FIELD_KEYS}
        lite_fields.append(lite)

        sheet = field.get("sheet", "UNKNOWN")
        stats["total"] += 1
        stats["sheets"][sheet] = stats["sheets"].get(sheet, 0) + 1
        if field.get("vietcap_mapped"):
            stats["mapped"] += 1
        else:
            stats["unmapped"] += 1

    lite_schema = {
        "version": full.get("version", "5.0"),
        "description": "Lite schema for pipeline runtime — stripped of sample_values & metadata",
        "generated_at": "2026-03-05",
        "total_fields": stats["total"],
        "mapped_fields": stats["mapped"],
        "unmapped_fields": stats["unmapped"],
        "sheet_counts": full.get("sheet_counts", stats["sheets"]),
        "fields": lite_fields
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(lite_schema, f, ensure_ascii=False, separators=(",", ":"))

    # Report
    full_size_kb  = os.path.getsize(INPUT_PATH)  / 1024
    lite_size_kb  = os.path.getsize(OUTPUT_PATH) / 1024
    reduction_pct = (1 - lite_size_kb / full_size_kb) * 100

    print(f"lite_schema.json created: {OUTPUT_PATH}")
    print(f"  Full schema : {full_size_kb:>8.1f} KB")
    print(f"  Lite schema : {lite_size_kb:>8.1f} KB")
    print(f"  Reduction   : {reduction_pct:>7.1f}%")
    print(f"  Total fields: {stats['total']}")
    print(f"  Mapped      : {stats['mapped']}  (vietcap_mapped=True)")
    print(f"  Unmapped    : {stats['unmapped']}")
    print(f"\n  Sheet breakdown:")
    for sheet, count in sorted(stats["sheets"].items()):
        print(f"    {sheet:<15} : {count} fields")

if __name__ == "__main__":
    build_lite_schema()

