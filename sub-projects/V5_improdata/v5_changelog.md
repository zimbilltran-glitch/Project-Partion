# 📝 V5 ImproData Changelog

Mọi thay đổi liên quan đến cấu trúc source code, dữ liệu, hoặc kiến trúc của tính năng V5 (Data Integrity Enhancement) sẽ được ghi chú ở đây để các Agent đồng bộ.

## [Unreleased]
### Added
- Khởi tạo dự án V5 `V5_improdata`.
- Thiết lập bộ Management Files (Plan, Task, Changelog, Challenges, Findings).
- Root cause analysis: xác định `vietcap_key` trống trong `golden_schema.json` gây sai dữ liệu.

### Discovered (Phát hiện)
- **100% field CDKT/KQKD/LCTT** (normal company) có `vietcap_key: ""` trong `golden_schema.json`.
- Chỉ **10 field** có hardcoded override trong `providers/vietcap.py`.
- Fallback logic `f"bsa{idx}"` → sai prefix cho Nợ/Vốn (`bsb`), Bank IS (`isb`), Bank CF (`cfb`).
- Dữ liệu FPT trên Supabase **không khớp** Vietcap web ở nhiều dòng (ví dụ: Phải trả người bán, Thuế, Nguyên giá TSCÐ).
