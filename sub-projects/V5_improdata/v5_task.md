# 📋 V5 Task Tracker — Data Integrity Enhancement (ImproData)

> **Thư mục Project**: `sub-projects/V5_improdata`
> **Kế hoạch**: `v5_implementation_plan.md`
> **Trạng thái**: ✅ Hoàn thành 100%

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
- [x] **P3.1**: Chạy `pipeline.py` cho FPT (ticker pilot) với schema mới.
- [x] **P3.2**: So sánh kết quả Parquet mới với dữ liệu Vietcap web (spot check 12 field).
- [x] **P3.3**: Nếu pass → Chạy `sync_supabase.py` cho toàn bộ VN30.
- [x] **P3.4**: Xác nhận accounting identity: `Tổng TS = Nợ PT + Vốn CSH` (tolerance ±0.01%).

## 🧪 Phase 4: Test (Validation & Audit)
- [x] **P4.1**: Viết script `validate_vs_web.py` — so sánh Supabase vs API cho toàn bộ VN30 (Đã thực hiện qua `validate_full.py`).
    - [x] Run `validate_full.py` on all 30 tickers
    - [x] Record results in `_validation_full_report.txt`
    - [x] Achieve 100% accounting identity match (0% Diff)
    - [x] Commit and push changes to Git (V5 completed)
- [x] **P4.2**: CFO Audit: Kiểm tra debit/credit rules, accounting identity (30/30 Pass).
- [x] **P4.3**: CTO Audit: Kiểm tra pipeline idempotent, log integrity.
- [x] **P4.4**: Release & Update Changelog.

## 🌟 PHASE 5 (TBD): DATA ENRICHMENT & FRONTEND FIX
- [ ] P5.1: Bổ sung `eps_ttm`, `week52_high`, `week52_low`, và định giá CFO (P/E, P/B) vào `company_overview`.
- [ ] P5.2A: Tính toán CSTC cho Phi Tài Chính (Biên lãi ròng, Vay ngắn hạn, Phải trả người bán, Mua trả trước, Vốn góp).
- [ ] P5.2B: Tính toán CSTC cho Bank (CASA, YOEA, Tỷ lệ nợ xấu, ROA, ROE, Vốn CSH).
- [ ] P5.3: Cập nhật frontend để ánh xạ đúng data chart ("Cấu trúc tài sản", "Lịch sử nợ") cho nhóm Chứng Khoán (SEC).
- [ ] P5.4: Cập nhật `calc_snowflake.py` để chấm lại điểm 5 chiều chính xác.
- [ ] P5.5: QA Audit xác nhận 100% biểu đồ không còn 0/null.
