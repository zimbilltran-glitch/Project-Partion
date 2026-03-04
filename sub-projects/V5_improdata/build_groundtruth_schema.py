import json
import os

SCHEMA_PATH = "c:/Users/Admin/OneDrive/Learn Anything/Antigravity/2.Project v2/sub-projects/Version_2/golden_schema.json"

# Ground Truth Map: field_id -> {sector: vietcap_key}
GROUND_TRUTH = {
    # INCOME STATEMENT (KQKD)
    "kqkd_doanh_thu_thuan": {"normal": "isa3", "sec": "isa3", "bank": "isb27"},
    "kqkd_loi_nhuan_gop": {"normal": "isa5", "sec": "isa5", "bank": "isb30"},
    "kqkd_chi_phi_ban_hang": {"normal": "isa9", "sec": "iss150"},
    "kqkd_chi_phi_quan_ly_doanh_nghiep": {"normal": "isa10", "sec": "iss151", "bank": "isb39"},
    "kqkd_chi_phi_tai_chinh": {"normal": "isa8", "sec": "iss152"},
    "kqkd_lai_truoc_thue": {"normal": "isa16", "sec": "isa16", "bank": "isa16"},
    "kqkd_lai_thuan_sau_thue": {"normal": "isa20", "sec": "isa20", "bank": "isa20"},
    "kqkd_loi_nhuan_cua_co_dong_cua_cong_ty_me": {"normal": "isa22", "sec": "isa22", "bank": "isa22"},
    "kqkd_eps": {"normal": "isa23", "sec": "isa23", "bank": "isa23"},
    
    # BALANCE SHEET (CDKT)
    "cdkt_tien_va_tuong_duong_tien": {"normal": "bsa2", "sec": "bsa2", "bank": "bsb94"},
    "cdkt_tong_cong_tai_san": {"normal": "bsa53", "sec": "bsa53", "bank": "bsa53"},
    "cdkt_no_phai_tra": {"normal": "bsa54", "sec": "bsa54", "bank": "bsa54"},
    "cdkt_von_chu_so_huu": {"normal": "bsa78", "sec": "bsa78", "bank": "bsa78"},
    "cdkt_tong_cong_nguon_von": {"normal": "bsa96", "sec": "bsa96", "bank": "bsa96"},
    
    # CASH FLOW (LCTT)
    "lctt_luu_chuyen_tien_thuan_tu_hoat_dong_kinh_doanh": {"normal": "cfa18", "sec": "cfa18", "bank": "cfb75"},
    "lctt_luu_chuyen_tien_thuan_tu_hoat_dong_dau_tu": {"normal": "cfa35", "sec": "cfa35", "bank": "cfb76"},
    "lctt_luu_chuyen_tien_thuan_tu_hoat_dong_tai_chinh": {"normal": "cfa40", "sec": "cfa40", "bank": "cfb77"},
    "lctt_luu_chuyen_tien_thuan_trong_ky": {"normal": "cfa38", "sec": "cfa38", "bank": "cfb79"},
    
    # Sector Specific Overrides (to match metrics.py expectations)
    "kqkd_bank_thu_nhap_lai_thuan": {"bank": "isb27"},
    "kqkd_bank_tong_thu_nhap_hoat_dong": {"bank": "isb36"},
    "cdkt_bank_tong_tai_san": {"bank": "bsa53"},
    "cdkt_bank_cho_vay_khach_hang": {"bank": "bsa16"}, # Re-check image for MBB loan key
    "cdkt_sec_tong_cong_tai_san": {"sec": "bsa53"},
    "kqkd_sec_doanh_thu_hoat_dong": {"sec": "isa3"}
}

def build():
    if not os.path.exists(SCHEMA_PATH):
        print(f"Error: {SCHEMA_PATH} not found")
        return

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    mapped_count = 0
    cleared_count = 0
    ground_truth_ids = set(GROUND_TRUTH.keys())

    for field in schema["fields"]:
        fid = field["field_id"]
        if fid in GROUND_TRUTH:
            field["vietcap_key"] = GROUND_TRUTH[fid]
            mapped_count += 1
        else:
            if field.get("vietcap_key") is not None:
                field["vietcap_key"] = None
                cleared_count += 1

    with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    print(f"Success!")
    print(f"  Mapped:  {mapped_count} (Ground Truth)")
    print(f"  Cleared: {cleared_count} (Unverified)")
    print(f"  Total mapped in schema: {mapped_count}")

if __name__ == "__main__":
    build()
