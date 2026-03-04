# 📋 V5 Task Tracker — Data Integrity Enhancement (ImproData)

> **Thư mục Project**: `sub-projects/V5_improdata`
> **Kế hoạch**: `v5_implementation_plan.md`
> **Trạng thái**: 🔧 Phase 5 đang sửa lỗi regression

---

## ✅ Phase 1: Blueprint (Khảo sát & Chuẩn bị)
- [x] **P1.0**: Tạo môi trường V5 (`v5_implementation_plan.md`, `v5_task.md`, `v5_changelog.md`...)
- [x] **P1.1**: Phân tích cấu trúc API response của Vietcap (key prefix: `bsa`/`bsb`/`bss`/`bsi`).
- [x] **P1.2**: So sánh dữ liệu Supabase hiện tại với raw API (dùng FPT làm mẫu kiểm chứng).
- [x] **P1.3**: Xác nhận tất cả `vietcap_key` trong `golden_schema.json` — đánh dấu trống vs có giá trị.

## ✅ Phase 2: Layer (Sửa lỗi mapping — Golden Schema)
- [x] **P2.1**: Viết script `rebuild_schema_keys.py` — auto-discover đúng key cho mỗi field từ raw API.
- [x] **P2.2**: Chạy script → cập nhật toàn bộ `vietcap_key` trong `golden_schema.json`.
- [x] **P2.3**: Xóa hardcoded `field_mapping` trong `providers/vietcap.py` (10 override cũ).
- [x] **P2.4**: Xóa logic fallback positional `f"bsa{sheet_row_idx}"`.

## ✅ Phase 3: Assemble (Re-sync & Verify)
- [x] **P3.1**: Chạy `pipeline.py` cho FPT (ticker pilot) với schema mới.
- [x] **P3.2**: So sánh kết quả Parquet mới với dữ liệu Vietcap web (spot check 12 field).
- [x] **P3.3**: Nếu pass → Chạy `sync_supabase.py` cho toàn bộ VN30.
- [x] **P3.4**: Xác nhận accounting identity: `Tổng TS = Nợ PT + Vốn CSH` (tolerance ±0.01%).

## ✅ Phase 4: Test (Validation & Audit)
- [x] **P4.1**: Viết script `validate_vs_web.py` — so sánh Supabase vs API cho toàn bộ VN30.
    - [x] Run `validate_full.py` on all 30 tickers
    - [x] Record results in `_validation_full_report.txt`
    - [x] Achieve 100% accounting identity match (0% Diff)
    - [x] Commit and push changes to Git (V5 completed)
- [x] **P4.2**: CFO Audit: Kiểm tra debit/credit rules, accounting identity (30/30 Pass).
- [x] **P4.3**: CTO Audit: Kiểm tra pipeline idempotent, log integrity.
- [x] **P4.4**: Release & Update Changelog.

## 🌟 PHASE 5: DATA ENRICHMENT & FRONTEND FIX

### Đã hoàn thành
- [x] P5.1: Bổ sung `eps_ttm`, `week52_high`, `week52_low`, và định giá CFO (P/E, P/B) vào `company_overview`.
- [x] P5.3: Cập nhật frontend chart fallbacks cho nhóm SEC (`FinancialPositionChart.jsx`, `DebtEquityHistoryChart.jsx`).
- [x] P5.4: Tính toán lại điểm Snowflake (360 độ) — `calc_snowflake.py` đã chạy cho 31 mã.

### ⚠️ P5.2: CSTC Regression — CẦN SỬA
> **Bug phát hiện**: Script `calculate_cstc.py` chỉ tính 7 chỉ số cơ bản và có lỗi đơn vị, 
> đã ghi đè lên tab "Chỉ số tài chính" khiến mất 40+ metrics gốc.

- [x] P5.2-DIAG: Phân tích root cause (xong — xem phần bug analysis bên dưới)
- [/] P5.2-FIX: Chạy lại `metrics.py` (engine tính 40+ chỉ số) cho toàn bộ 30 mã VN30
    - Script: `run_metrics_batch.py` hoặc `re_sync_ratios.py`
    - Vấn đề: Script bị hang do import chain (`pipeline.py` → `security.py` → blocking cipher)
    - [ ] Sửa import chain hoặc tách logic `metrics.py` khỏi `security.py`
    - [ ] Chạy thành công cho 30 mã × 2 period (year + quarter)
    - [ ] Verify FPT có 40+ item_ids trong `financial_ratios_wide` (không còn 7)

### P5.5: Frontend UI QA Audit
- [ ] P5.5: Audit UI cuối cùng sau khi data đã fix xong

---

## 🐛 Bug Analysis (Phase 5 Regression)

### Bug 1: ROE/ROA/Net Margin = 0
- **Script**: `calculate_cstc.py`
- **Nguyên nhân**: Unit mismatch — parquet lưu `net_income=4944` (Tỷ VND) nhưng `equity=35.7T` (VND đồng)
- **Kết quả**: `ROE = 4944 / 35,727,540,104,800 ≈ 0.0%`

### Bug 2: Growth (g7_1, g7_2) = 0%
- g7_1/g7_2 chỉ có data cho 6 mã legacy (KDH, PDR, VHC...), chưa tính cho VN30
- `metrics.py` tính sẵn g7_1/g7_2 nhưng chưa được chạy cho VN30

### Bug 3: Bank metrics (NIM, CASA, NPL) trống
- bank_4_* items do `metrics.py` tính từ Supabase data, nhưng chưa chạy cho VN30 banks

### Bug 4: Tab "Chỉ số tài chính" bị strip
- `calculate_cstc.py` **xóa** toàn bộ `financial_ratios` cũ rồi chèn chỉ 7 rows
- VHC (legacy) vẫn có 40+ rows vì không nằm trong danh sách VN30 của script
- FPT (VN30) chỉ còn 7 rows → tab hiển thị thiếu hoàn toàn

### Giải pháp
- Chạy `metrics.py` (via `re_sync_ratios.py`) cho 30 mã → khôi phục 40+ metrics
- `metrics.py` đọc từ Supabase (không có bug đơn vị) và tính đầy đủ cho mọi sector
