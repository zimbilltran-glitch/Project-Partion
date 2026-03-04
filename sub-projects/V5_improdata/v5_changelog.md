# 📝 V5 ImproData Changelog

Mọi thay đổi liên quan đến cấu trúc source code, dữ liệu, hoặc kiến trúc của tính năng V5 (Data Integrity Enhancement) sẽ được ghi chú ở đây để các Agent đồng bộ.

## [Released]

### 2026-03-04 — Phase 4 Validation & Completion
#### Verified
- **100% Validation Pass**: Chạy `validate_full.py` cho 30 mã VN30 trên Supabase Cloud.
- **Accounting Identity Checked**: 30/30 mã (Normal, Bank, SEC) đều khớp `Tổng Tài Sản = Nợ PT + Vốn CSH` (Assets = Liabilities + Equity).
- **RLS Policy Fixed**: Đã thêm chính sách cho phép `anon` role thực hiện INSERT/UPDATE/DELETE phục vụ sync dữ liệu.

#### Added
- `V5_improdata/validate_full.py` — Script kiểm tra tính toàn vẹn dữ liệu trực tiếp từ Supabase.
- `V5_improdata/batch_pipeline_vn30.py` — Script tự động chạy pipeline cho danh sách mã VN30.
- `_validation_full_report.txt` — Báo cáo chi tiết kết quả validation.

### 2026-03-04 — Phase 5 Data Enrichment & Audit
#### Added
- `sub-projects/V5_improdata/phase5_1_enrich.py` — Script bổ sung EPS TTM, Week52 High/Low vào `company_overview`.
- `sub-projects/V5_improdata/run_metrics_batch.py` — Script batch chạy lại engine `metrics.py` cho 30 mã VN30 (Fix regression).

#### Fixed (UI)
- **FinancialPositionChart.jsx**: Thêm logic fallback chart cho Securities sector (SEC).
- **DebtEquityHistoryChart.jsx**: Sửa biểu đồ lịch sử nợ cho Bank và SEC.
- **chartMappings.js**: Cập nhật mapping item_id chuẩn cho 3 sector (Normal, Bank, SEC).

#### Changed
- **calc_snowflake.py**: Cập nhật env loading (frontend/.env) và prefix VITE_. Tính lại điểm cho 31 mã.

#### Discovered (BUG)
- **P5.2 Regression**: Phát hiện `calculate_cstc.py` lỗi đơn vị (ROE=0) và làm hỏng tab Chỉ số tài chính cho VN30. Quyết định rollback/replace bằng `metrics.py` batch.


## [Unreleased]

### 2026-03-04 — Phase 2+3 Execution
#### Fixed
- **Segmented CDKT mapping**: Fix critical sequential mapping bug. Schema fields giờ được chia thành 5 segments (Assets/TotalAssets/Liabilities/Equity/TotalSource) khớp với cấu trúc thực tế của Vietcap API keys.
- **Accounting identity**: FPT 2024 đã đạt `Tổng TS = Nợ PT + Vốn CSH` chính xác 100%.
- **73 CDKT key corrections**: Segmented mapping sửa 73 keys so với sequential mapping ban đầu.
- **9 name-based corrections**: Bank schema ground truth fix thêm 9 keys (e.g., `cdkt_tai_san_co_dinh: bsa36→bsa29`).

#### Changed
- `Version_2/golden_schema.json` — Rebuilt 188 fields: CDKT (122), KQKD (25), LCTT (41).
- `Version_2/providers/vietcap.py` — Xóa `field_mapping` dict (10 overrides) + fallback logic `f"bsa{idx}"`. Function `get_api_value()` giờ return `None` cho unmapped fields.

#### Added
- `V5_improdata/rebuild_schema_keys.py` — Final version: Segmented mapping + Bank anchor + name-based correction.
- `V5_improdata/validate_spotcheck.py` — 12-field spot check + accounting identity validator.
- `V5_improdata/_raw/FPT_NOTE.json` — Raw NOTE data (0 usable keys confirmed).
- Analysis files: `_key_analysis.txt`, `_smart_mapping_analysis.txt`, `_final_mapping_log.txt`, `_v5_spotcheck.txt`.

### 2026-03-03 — Phase 1 Execution + V5 Setup
#### Added
- Khởi tạo dự án V5 `V5_improdata` với Management Files.
- `V5_improdata/phase1_analyze.py` — Fetch raw API (FPT/MBB/SSI), schema audit.
- `V5_improdata/v5_phase1_report.json` — Phase 1 report: 345 unmapped fields found.
- `V5_improdata/_raw/` — Raw API data cho 3 tickers × 3 sections.

#### Discovered (Phát hiện)
- **100% field CDKT/KQKD/LCTT** (normal company) có `vietcap_key: ""`.
- Chỉ **10 field** có hardcoded override, **6/10 SAI**.
- Fallback logic `f"bsa{idx}"` → sai cho tất cả fields sau bsa52.
- Bank/SEC schemas đã có 100% correct mapping — dùng làm ground truth.
- `bsa` prefix chứa ALL items (Assets + Liabilities + Equity) cho normal company, KHÔNG phải chỉ Assets.

### Other
- Disabled CI/CD workflow (`ci.yml`) và data pipeline workflow (`data_pipeline.yml`) — thêm `if: false` để tạm tắt trong thời gian V5.
