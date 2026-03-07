# 📝 Finsang Master Changelog

Nhật ký thay đổi tập trung của toàn bộ dự án Finsang.

## [v6.2.0] - 2026-03-08
### Added
- **100% Data Integrity Mastery**: Hoàn tất mục tiêu độ chính xác tuyệt đối cho bộ 3 Sector đại diện (FPT, MBB, SSI).
- **Tool `fix_keys.py`**: Tự động hóa việc sửa lỗi mapping key của API Vietcap bằng cách so khớp dữ liệu thô với Excel Ground Truth.
- **JSON Interception Strategy**: Bắt gói tin JSON trực tiếp từ Web UI để bypass các lỗi cào DOM (HTML Scraping).
### Changed
- **VN30 Scale-up**: Đồng bộ lại dữ liệu cho toàn bộ 30 mã VN30 với bộ schema mới đã được verify 100%.

## [v6.1.1-security] - 2026-03-07
### Fixed (CTO Audit P0)
- **RLS Re-enabled**: Bật `ROW LEVEL SECURITY` trên bảng `financial_ratios` — đây là lỗi CRITICAL dữ liệu exposed toàn bộ ra internet.
- **Duplicate Policies Removed**: Xóa các `SELECT` policy trùng trên `balance_sheet`, `cash_flow`, `income_statement`, `financial_ratios`.
- **Anon Write Locked**: Thu hồi quyền `INSERT/UPDATE` của `anon` trên `company_overview` và `stock_ohlcv`.
- **SECURITY DEFINER → SECURITY INVOKER**: Recreate view `financial_ratios_wide` với `security_invoker=true`.
- **pandas Timeout Guard**: Thêm `read_excel_with_timeout()` (90s) vào `excel_data_auditor.py` — ngăn process treo vô hạn.

## [v6.1.0] - 2026-03-07
### Added
- **Sub-project `V6_Excel_Extractor`**: Khởi chạy thành công Master Controller & Playwright Bot tải dữ liệu Excel BCTC trực tiếp từ Vietcap. Xử lý trị dứt điểm bế tắc API 403 Forbidden của Thuyết minh Ngân hàng.
- **Data Ground Truth**: Hàm Validator so khớp Supabase (CFO_CALC_V2) vs Excel. Tự động đè các giá trị lỗi rỗng lấy được từ API bằng Ground Truth (CASA, NPL).
- **Automation & Scheduling**: Tích hợp Windows Task Scheduler (`scheduler.py`) chạy hàng tháng ngày 1 lúc 02:00 cùng logic state-machine pending audit chờ bot xử lý tự động toàn diện. Chạy command tay mở rộng `v6_master_controller.py --all-db-banks`.
### Changed
- **Frontend Priority**: Cập nhật Database View `financial_ratios_wide` để tự động ưu tiên nguồn `V6_EXCEL` đè lên `CFO_CALC_V2` nhằm đảm bảo số liệu chính xác 100% khi React dashboard phân loại, chống clone data theo object ID.

## [v5.1.0] - 2026-03-05
### Added
- **Sector Metrics (Phase 5.6)**: Hoàn tất bộ chỉ số chuyên biệt cho Ngân hàng (LDR, CIR) và Chứng khoán (Margin/Equity, CER).
- **Security Hardening**: Khóa quyền INSERT/UPDATE/DELETE cho role `anon` trên Supabase. Thêm `timeout=10` cho tất cả `requests`.
- **Ops Tooling**: Phát hành `QUARTERLY_UPDATE_GUIDE.md` cho quy trình bảo trì dữ liệu hàng quý.
- **Production Build**: Biên dịch Frontend thành công (`dist/` folder).
### Changed
- **Pipeline Performance (Phase 5.5)**: Chuyển đổi sang `ThreadPoolExecutor` và `lite_schema.json`. Tốc độ resync VN30 tăng ~98x (từ 45p xuống 28s).
- **Master Docs Update**: Cập nhật toàn bộ hệ thống file điều khiển (`.md`) để phản ánh trạng thái hoàn tất của Giai đoạn 5.

## [v5.0.0] - 2026-03-05
### Added
- **Sub-project `V5_improdata`**: Khắc phục lỗi dữ liệu Positional Mapping.
- Kỹ thuật **Exact Ground Truth Mapping** cho độ chính xác dữ liệu gốc 100%.
### Changed
- CTO Audit: Đánh giá Performance (67/100). Đặt ra kế hoạch tái cấu trúc Async Pipeline và rút gọn `lite_schema.json`.

## [v4.0.0] - 2026-03-03
### Added
- **Sub-project `V4_Chart_Improve`**: Khởi tạo thư mục và chuỗi file Management chuẩn B.L.A.S.T cho luồng vẽ biểu đồ nâng cao.
- **Documents**: Ra mắt `Finsang_Master_Changelog.md` và `Finsang_Master_Active_Roadmap.md` để việc theo dõi vĩ mô trực quan hơn.
### Changed
- Đổi tên `Finsang_Team_Guide.md` => `Finsang_Master_Team_Guide.md`.
- Đổi tên `findings.md` => `Finsang_Master_Findings.md` để đồng nhất naming convention toàn hệ thống.
- Cập nhật Reference Docs trong `README.md`.

## [v3.0.0] - 2026-03-01
### Added
- **Sub-project `V3_SimplyWallSt`**: Tính năng Overview 360 độ phong cách quỹ đầu tư.
- **Frontend**: Component mới (Snowflake, Gauge, PriceChart). Dùng kỹ thuật đồ họa SVG thuần.
- **Data Enrichment**: Fetch giá OHLCV VN30. Tự động tính toán Snowflake Scores (5 chiều).
### Security
- Cập nhật RLS Policy trên Supabase cho `company_overview`.

## [v2.0.0] - 2026-02-25
### Added
- Khởi chạy Dashboard React Vite đầu tiên (OLED Theme).
- Mô hình lập trình B.L.A.S.T Framework.
- Engine Data ETL từ Vietcap chuyển sang Parquet nội bộ. Cải thiện thuật toán bắt Absolute Row Index chống "Index Drift".

## [v1.0.0] - 2026-02-21
### Added
- Bản Prototype đầu tiên dùng Playwright cào Fireant (Đã chính thức **DEPRECATED**).
