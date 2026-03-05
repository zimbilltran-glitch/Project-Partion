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

- [x] P5.2-DIAG: Phân tích root cause (Fix YOEA typo, identify CASA missing Note data)
- [x] P5.2-FIX: Chạy lại `metrics.py` cho toàn bộ 31 mã VN30 (HOÀN TẤT)
- [x] Sửa import chain: Viết `run_metrics_batch.py` + `sb_client.py` (Singleton)
- [x] Chạy thành công cho 31 mã (Tất cả quarters)
- [x] Verify FPT có 40+ item_ids trong `financial_ratios_wide`
- [x] Cập nhật findings về CASA (Missing NOTE sync)
- [x] P5.5: Audit UI cuối cùng (Check NIM, YOEA, LDR, CIR, Margin/Equity) - ✅ ALL PASS

## 🚨 PHASE 5.3: EXACT GROUND TRUTH MAPPING
> **Chuyển đổi từ trượt dòng vị trí (Positional) sang khớp cứng Ground Truth Map.**

- [x] **P5.3.1**: Truncate/Xóa dữ liệu sai lệch hiện tại trên hệ thống (Supabase DB).
- [x] **P5.3.2**: Viết `build_groundtruth_schema.py` cập nhật 22+ keys tĩnh đúng nhất vào `vietcap_key`. Xóa các key không xác minh.
- [x] **P5.3.3**: Cập nhật logic để hỗ trợ chạy batch toàn bộ VN30 tự động (`v5_full_resync.py`).
- [x] **P5.3.4**: Chạy Resync toàn bộ VN30 từ đầu để nạp dữ liệu sạch.
- [x] **P5.3.5**: Chạy `sync_supabase.py` sinh các bảng tài chính mở rộng (financial_ratios) trơn tru, verify FPT, MBB.

## ✅ PHASE 5.6: SECTOR METRICS & LIMITATIONS
- [x] **P5.6.1**: Dò tìm API Keys cho phần NOTE (403 Forbidden detected)
- [x] **P5.6.2**: Tính toán LDR, CIR (Bank) và Margin/Equity (SEC) thành công.
- [x] **P5.6.3**: Xác nhận giới hạn CASA (Technical Debt due to 403 NOTE API).
- [x] **P5.6.4**: Hoàn tất Security Hardening (RLS + Timeout).
- [x] **P5.6.5**: Phát hành QUARTERLY_UPDATE_GUIDE.md.

## ✅ PHASE 5.7: CFO AUDIT & DATA INTEGRITY (BL-2, BL-3)
- [x] **P5.7.1**: Viết script `cfo_audit_bl2_bl3.py` kiểm tra đẳng thức kế toán.
- [x] **P5.7.2**: Verify BL-2 (Assets = Liab + Equity) — 🟢 **PASSED** cho VN30.
- [x] **P5.7.3**: Verify BL-3 (Net CF = Op + Inv + Fin) — ✅ **RESOLVED**.
    - [x] Fixed BL-3 Cash Flow Identity Gap (FPT 2024 pass, MBB 2024 pass, SSI pass).
    - [x] Probed Vietcap API for correct keys (`cfa36` for Op, `cfb79` for Net Bank, etc.).
- [x] **P5.7.4**: Fix mapping LCTT in `lite_schema.json` and run full resync LCTT.
    - [x] Updated `lite_schema.json` mapping.
    - [x] Verified with `cfo_audit_bl2_bl3.py`.

---

## 🐛 Bug Analysis (Phase 5 Regression)

### Bug 1: ROE/ROA/Net Margin = 0 ✅ FIXED
- **Script**: `run_metrics_batch.py` (via `metrics.py`)
- **Nguyên nhân**: Unit mismatch trong `calculate_cstc.py`.
- **Giải pháp**: Dùng toolkit `metrics.py` đọc trực tiếp từ DB để đảm bảo unit consistent.

### Bug 2: Growth (g7_1, g7_2) = 0% ✅ FIXED
- Đã tính toán lại cho toàn bộ 31 mã VN30.

### Bug 3: Bank metrics (NIM, CASA, NPL) trống ✅ RESOLVED
- **YOEA/NIM**: ✅ Fixed typo key.
- **CASA**: ⚠️ Bị giới hạn (Noted as limitation).

### Bug 4: Tab "Chỉ số tài chính" bị strip ✅ FIXED
- Đã khôi phục 40+ rows cho mỗi mã VN30 thông qua `metrics.py`.

### Bug 5: Cash Flow Identity Gap (BL-3) ✅ RESOLVED
- **Giải pháp**: Fixed via `fix_bl3_mapping_v2.py`. Verified for FPT, SSI, MBB.

### Giải pháp Tổng thể
- Đã chạy `run_metrics_batch.py` thành công cho 31 mã VN30. Dữ liệu CSTC đã đầy đủ và chuẩn xác.
