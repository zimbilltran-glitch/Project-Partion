# 📋 V5 Task Tracker — Data Integrity Enhancement (ImproData)

> **Thư mục Project**: `sub-projects/V5_improdata`
> **Kế hoạch**: `v5_implementation_plan.md`
> **Trạng thái**: 🚀 Bắt đầu

---

## ✅ Phase 1: Blueprint (Khảo sát & Chuẩn bị)
- [x] **P1.0**: Tạo môi trường V5 (`v5_implementation_plan.md`, `v5_task.md`, `v5_changelog.md`...)
- [x] **P1.1**: Phân tích cấu trúc API response của Vietcap (key prefix: `bsa`/`bsb`/`bss`/`bsi`).
- [x] **P1.2**: So sánh dữ liệu Supabase hiện tại với raw API (dùng FPT làm mẫu kiểm chứng).
- [x] **P1.3**: Xác nhận tất cả `vietcap_key` trong `golden_schema.json` — đánh dấu trống vs có giá trị.

## 🔧 Phase 2: Layer (Sửa lỗi mapping — Golden Schema)
- [x] **P2.1**: Viết script `rebuild_schema_keys.py` — auto-discover đúng key cho mỗi field từ raw API.
- [x] **P2.2**: Chạy script → cập nhật toàn bộ `vietcap_key` trong `golden_schema.json`.
- [x] **P2.3**: Xóa hardcoded `field_mapping` trong `providers/vietcap.py` (10 override cũ).
- [x] **P2.4**: Xóa logic fallback positional `f"bsa{sheet_row_idx}"`.

## 🔄 Phase 3: Assemble (Re-sync & Verify)
- [ ] **P3.1**: Chạy `pipeline.py` cho FPT (ticker pilot) với schema mới.
- [ ] **P3.2**: So sánh kết quả Parquet mới với dữ liệu Vietcap web (spot check 10 field).
- [ ] **P3.3**: Nếu pass → Chạy `sync_supabase.py` cho toàn bộ VN30.
- [ ] **P3.4**: Xác nhận accounting identity: `Tổng TS = Nợ PT + Vốn CSH` (tolerance ±0.01%).

## 🧪 Phase 4: Test (Validation & Audit)
- [ ] **P4.1**: Viết script `validate_vs_web.py` — so sánh Supabase vs API cho toàn bộ VN30.
- [ ] **P4.2**: CFO Audit: Kiểm tra debit/credit rules, accounting identity.
- [ ] **P4.3**: CTO Audit: Kiểm tra pipeline idempotent, log integrity.
- [ ] **P4.4**: Release & Update Changelog.
