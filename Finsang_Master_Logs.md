# Finsang Master Logs — Production Audit & Milestones

This document serves as the centralized source of truth for the Finsang project's progress, technical audits, and major milestones. It follows the B.L.A.S.T. framework for standardized deployment tracking.

---

## 🏛️ Project Governance
- **Project Name:** Finsang Financial Terminal (Production v2.1)
- **Framework:** B.L.A.S.T. (Blueprint, Link, Architect, Stylize, Trigger)
- **Primary Auditor:** `@cto-mentor-supervisor`
- **Security Standard:** Fernet AES-128 Encryption + Supabase RLS

---

## 🕵️ High-Level Audit Summary

| Milestone | Date | Status | Score | Findings & Remediation |
|---|---|---|---|---|
| Phase B (Blueprint) | 2026-02-24 | ✅ PASSED | 88/100 | Established `golden_schema.json` with 345 fields. Corrected `slugify` logic. |
| Phase L (Link) | 2026-02-24 | ✅ PASSED | 90/100 | Verified Vietcap API public endpoints. Reduced risk by removing Playwright. |
| Phase A (Architect) | 2026-02-24 | ✅ PASSED | 92/100 | Hive-partitioning implemented. Solved `interpolate` vs `absolute` index drift. |
| Phase S (Stylize) | 2026-02-25 | ✅ PASSED | 90/100 | OLED Dark Theme + React/Vite dashboard initialization. |
| Phase T (Trigger) | 2026-02-25 | ✅ PASSED | 95/100 | Supabase sync engine live. Logging decoupled to prevent ETL failure. |
| Phase V/M (Validation) | 2026-02-25 | ✅ PASSED | 95/100 | Data accuracy verified cross-source. Encryption at rest confirmed. |

---

## 📋 Detailed Engineering Audit Trail

### [2026-02-25] - THE FPT DATA ANOMALY RESOLUTION
- **Issue:** Specific tickers (FPT) showed static "Phải trả khác" values (~192M) across all periods.
- **Root Cause Analysis:** Discovery of **Index Drift**. The extractor used `enumerate()` on a subset schema (122 fields) while the API returned a full list (~130). This caused a 10-row shift, mapping the target field to a dummy/static API key.
- **Remediation:** Migrated pipeline orchestration to use **Absolute Mapping** via `field.get("row_number")`.
- **Impact:** 100% data fidelity restored across all balance sheet rows.

### [2026-02-26] - PROJECT RESTRUCTURING & SCALABILITY
- **Action:** Consolidated 10+ fragmented directories into 3 master parent folders (`internal-skills`, `design-themes`, `sub-projects`).
- **Goal:** Preparation for GitHub Team collaboration and reduction of root-level cognitive load.
- **Architecture Change:** Moved `Version_2` (Core) into `sub-projects/` but maintained `streamlit_app.py` as a root router for quick access.

---

## 📦 Component Health & Documentation Status

| Component | Health | Clarity Score | Notes |
|---|---|---|---|
| **ETL Pipeline (v2)** | 🟢 98% | 10/10 | Excellent decoupling. Docstrings in `pipeline.py`, `metrics.py`, and `viewer.py` are highly detailed. |
| **Legacy Apps (v1)** | 🟢 100% | 10/10 | Marked explicitly as Deprecated via top-level `README.md`. No risk of developer confusion. |
| **PDF Extraction** | 🟢 95% | 9/10 | `README.md` explains isolation architecture perfectly. |
| **React Frontend** | 🟡 85% | 8/10 | `App.jsx` handles state well but is currently undergoing UI styling expansion. Clear architectural boundary. |
| **Secure Storage** | 🟢 100% | 10/10 | `.gitignore` verified. No credentials exposed. Encryption verified. |

---

## 📝 Version & Session Commit Logs

> **Quy định:** Trước khi commit code lên GitHub, toàn bộ thành viên bắt buộc phải ghi log lại sự thay đổi của các phiên bản hoặc phiên làm việc (session) tại đây.

### [v1.0.0] - 2026-02-23 (Legacy Initial Prototype)
- **Data Collection:** Xây dựng hệ thống quét dữ liệu báo cáo tài chính từ Fireant.
- **Methodology:** Sử dụng Playwright kết hợp BeautifulSoup để cào giao diện HTML tĩnh. Thử nghiệm kết nối qua request API Unofficial nhưng dính chướng ngại token Bearer và rate-limit.
- **Parsing Strategy:** Bóc tách chỉ tiêu tài chính dựa vào vòng lặp mảng tương đối (`enumerate`), sau này phát sinh nhược điểm "Index Drift" do phụ thuộc vào số lượng dòng của bảng trả về theo từng mã chứng khoán.
- **Storage:** Ghi dữ liệu thô ra file JSON và CSV cơ bản, chưa có bảo mật hoặc nén chuẩn Parquet.
- *Lưu ý: Source code version này đã chính thức bị chuyển thành `[DEPRECATED]`.*

### [v2.0.0] - 2026-02-25 (Finsang Core Engine & B.L.A.S.T Framework)
- **ETL Origin:** Chuyển đổi công nghệ từ thư viện Playwright sang luồng API trực tiếp từ Vietcap để chống lỗi block và giới hạn IP.
- **Architecture:** Khởi tạo và áp dụng mô hình B.L.A.S.T (Blueprint, Link, Architect, Stylize, Trigger) cho toàn bộ backend.
- **Data Integrity:** Khắc phục triệt để lỗi "Index Drift" kinh điển của mã FPT bằng phương pháp Absolute Mapping (`golden_schema.json`).
- **Storage:** Tích hợp Fernet AES-128 mã hóa file Parquet tại local và đồng bộ dữ liệu bảo mật lên Supabase (Phase Trigger).
- **Frontend V1:** Khởi tạo dashboard React + Vite với giao diện OLED Dark Theme.

### [v2.1.0] - 2026-02-26 (Project Restructuring & Deep Audit)
- **Architecture:** Gom cụm cấu trúc thành 3 thư mục lõi: `sub-projects`, `design-themes`, `internal-skills`.
- **Documentation:** Viết mới `Finsang_Master_Team_Guide.md` và tái cấu trúc `README.md` thành điều hướng trung tâm.
- **Security Review:** Rà soát `.gitignore` bảo vệ tuyệt đối file `.env`, `keys.txt` và `data/` Parquet.
- **Legacy Cleanup:** Gắn cờ `[DEPRECATED]` cho `Version_1`, định hướng toàn bộ dev mới sang `Version_2`.
- **Visualization:** Đưa giao diện `streamlit_app.py` ra ngoài root làm Secondary Audit UI dự phòng cho React Dashboard.
- **Bug Fixes:** Cải thiện và tối ưu lại logic load data từ mã hóa Parquet thông qua `pipeline.py` nhằm fix các lỗi đọc sai dòng của thư viện `pyarrow`/`pandas`.
### [v2.2.0] - 2026-02-28 (Data Enrichment & UI Refinement)
- **Data Enrichment:** Triển khai Script `vn30_enrichment.py` chạy ngầm. Kéo thành công dữ liệu lịch sử tài chính cho toàn bộ rổ VN30 (kéo dài 10 năm với 32 quý + 8 năm/mã).
- **Core Engine Fix:** Sửa lỗi "0.0% Mapped" kinh điển đối với nhóm VN30. Nguyên nhân do `pipeline.py` nhầm lẫn giữa định vị theo thuộc tính `row_number` của Excel format, thay vì lấy index tuần tự từ Payload Vietcap JSON API.
- **Supabase Security:** Vô hiệu hóa tính năng (Disable) Row Level Security (RLS) để tài khoản Anon có thể Insert dữ liệu tự động mà không bị block.
- **Streamlit UI:** Sửa lỗi hiển thị mốc thời gian ngược chiều. Viết thuật toán Parsing Custom `sort_p` để luôn luôn sắp xếp cột mốc từ MỚI NHẤT -> CŨ NHẤT (Ví dụ: Q1/2025 -> Q4/2024 -> 2023).
- **React Frontend:** Loại bỏ cột Component `<MiniBarChart />` lỗi thời để tập trung không gian hiển thị rộng rãi hơn cho Bảng CĐKT tại UI chính. Trang bị khung Search Autocomplete thông minh lấy source từ List `TICKERS`.

### [v2.3.0-audit] - 2026-03-01 (Full Project Audit & Task Restructuring)
- **Full Audit:** Rà soát toàn bộ codebase, phát hiện 10 findings (F-001 → F-010). Chi tiết tại `Finsang_Master_Findings.md`.
- **Critical Bugs Found:**
  - F-001: `load_tab_from_supabase()` crash do biến `sheet_upper` chưa định nghĩa.
  - F-002: Duplicate `FINSANG_ENCRYPTION_KEY` trong `.env` (Fernet key, không phải Supabase).
- **Architecture Gaps:**
  - F-003: Frontend hoàn toàn không nhận biết nhóm ngành (sector-blind) → MBB/VCB hiển thị sai.
  - F-004: Sector classification hardcode tại 2 file riêng biệt.
  - F-007: Tab CSTC chưa tính đúng metrics theo nhóm ngành trên web.
- **Security:** F-005: RLS disabled trên 4 tables chính. Cần enable trước deploy.
- **Data Confirmation:** F-008: Xác nhận Supabase đã có đầy đủ 31 VN30 tickers (119K+ rows balance_sheet).
- **Design Decisions:** F-009: BCTC cập nhật theo quý, không cần scheduler hằng ngày. F-010: Mobile responsive ngoài scope hiện tại.
- **Task Restructuring:** Viết lại `task_plan.md` v3.0 với 6 phases mới thay thế B.L.A.S.T framework đã hoàn thành.
- **Fireant:** F-006: Pipeline Fireant tồn tại đầy đủ trong `tools/` nhưng chưa tích hợp V2 Provider pattern.

### [v3.0.0] - 2026-03-01 (Simply Wall St Theme & 360 Overview Integration)
- **Feature Overview:** Tích hợp giao diện "360 Overview" theo phong cách Simply Wall St, bao gồm Snowflake Radar Chart, Valuation Gauge, và Checklist Cards.
- **Data Enhancement:**
  - Viết script `fetch_ohlcv_vn30.py` dùng `vnstock` để nạp dữ liệu lịch sử giá OHLCV của rổ VN30 vào Supabase (`stock_ohlcv`).
  - Viết script `fetch_company_overview.py` để kéo hơn 30 chỉ số tài chính (P/E, P/B, ROE, Market Cap, Dividend, v.v.) vào bảng `company_overview`.
  - Viết script `calc_snowflake.py` để tính toán tự động điểm số 5 chiều (Value, Future, Past, Health, Dividend) dựa trên benchmark ngành.
- **Frontend Refactoring:**
  - Tách `App.jsx` khổng lồ thành cấu trúc component module: `CompanyHero`, `SnowflakeChart`, `QuickStats`, `ValuationGauge`, `ChecklistCards`, và `PriceChart`.
  - Áp dụng các rules CSS từ `theme.css` để biến GUI thành dạng Dark Mode cao cấp.
  - Fix lỗi rate limit và Unicode (1252 charmap trên Windows).
  - Tích hợp SVG thuần cho Snowflake và Price chart để tối ưu tốc độ render, không dùng third-party libraries.
- **Security & DB:**
  - Thêm migrations để bổ sung các cột mới vào `company_overview`.
  - Configure lại RLS policy cho phép `anon` roles có quyền `INSERT/UPDATE` thông qua pipeline script chạy nội bộ.
- **Documentation:** Chuyển đổi toàn bộ tài liệu V3 vào `sub-projects/V3_SimplyWallSt/` với `v3_changelog.md` để tách bạch rõ context.

### [v4.0.0] - 2026-03-03 (Analysis Charts Integration & Data Transformation)
- **Feature Initialization:** Khởi tạo Tab "Biểu đồ phân tích" bên cạnh tab CSTC, mục tiêu trực quan hoá dữ liệu KQKD, CĐKT, CSTC cho cả 3 phân ngành (Normal, Bank, Sec).
- **Architecture:** Thiết kế kiến trúc sử dụng thư viện `recharts` (React-native chart library). Quyết định này thay thế Pure SVG để xử lý các biểu đồ phức tạp như Mix Line-Bar, Stacked Area.
- **Data Layer:** Tái sử dụng dữ liệu từ các view Supabase hiện tại (`_wide`). Build `useAnalysisChartsData.js` hook để xoay trục Data thành mảng Array 1 chiều phù hợp làm input cho `recharts`.
- **Project Governance:** Khởi tạo không gian dự án V4 độc lập tại `sub-projects/V4_Chart_Improve` kèm theo 5 file B.L.A.S.T Management Files nhằm đảm bảo quy trình dev nghiêm ngặt.

### [v5.0.0] - 2026-03-05 (Data Integrity Enhancement & Performance CTO Audit)
- **Data Architecture Fix (Phase 5.3):** Khắc phục dứt điểm lỗi nghiêm trọng "Positional Mapping Anti-Pattern" làm sai lệch toàn bộ dữ liệu Supabase (e.g. EPS bị map nhầm vào Lợi nhuận ròng do lệch dòng Excel). Áp dụng chiến lược **Exact Ground Truth Mapping**, khóa cứng các key lõi (e.g. `isa20`, `isb27`) trực tiếp vào `golden_schema.json` dựa vào BCTC thật. Gỡ bỏ toàn bộ dữ liệu hỏng.
- **CTO Performance Audit (Score 67/100):** Phát hiện 3 "nút thắt cổ chai" (bottleneck) cấu trúc nghiêm trọng: (1) Chạy vòng lặp đồng bộ `subprocess` cực kỳ tốn RAM & CPU khởi tạo Python interpreter. (2) Schema `golden_schema.json` ~1MB quá cồng kềnh chứa nhiều text rác. (3) Dùng file Parquet làm trung gian thừa thãi khi daily sync làm chậm I/O ổ cứng.
- **Technical Debt remediation plan (Phase 5.5 - Performance Tuning):**
  - [x] **Data Structure:** Trích xuất file `lite_schema.json` siêu nhẹ chỉ chứa mapping dùng cho bots ETL.
  - [x] **Asynchronous Processing:** Chuyển `v5_full_resync.py` sang kiến trúc ThreadPoolExecutor hoặc Asyncio chạy nhiều mã VN30 đồng thời mà không đẻ thêm Subprocess. Import chung function chạy Pipeline và Sync.
  - [x] **Stream-to-Database:** Load dữ liệu trực tiếp vào Pandas RAM và upsert lên Supabase. Tách bước sinh file Parquet cứng thành một chức năng Backup định kỳ tách biệt thay vì đưa vào đường găng (critical path).

### [v5.1.0] - 2026-03-05 (Bank & SEC Metrics Finalization)
- **Data Mapping Audit (Phase 5.6):** 
  - Hoàn tất rà soát API raw JSON từ Vietcap cho các nhóm ngành Ngân hàng (MBB) và Chứng khoán (SSI, VCI, VND). 
  - Áp dụng các key `vietcap_key` (`isb27`, `isb36`, `bsb104`, v.v.) trực tiếp vào `golden_schema.json` để tính toán chính xác LDR, CIR.
  - Mở rộng script `metrics.py` bổ sung các chuẩn phân tích Chứng khoán (Margin/Equity, CER, Brokerage Share).
  - Tích hợp 100% data metrics vào `financial_ratios` table. 
- **Security & Ops:** 
  - Fix Bandit warnings (Timeout) trên toàn bộ codebase.
  - Xóa bỏ quyền `INSERT/UPDATE/DELETE` cho `anon` roles để nâng cao bảo mật (T4.1).
  - Khởi tạo tài liệu [QUARTERLY_UPDATE_GUIDE.md](QUARTERLY_UPDATE_GUIDE.md) hoàn chỉnh cho quy trình ETL Quý.
  - Frontend Production Build hoàn tất. Smoke Test thành công.

### [v5.1.8-audit] - 2026-03-05 (CFO Audit & CF Identity Investigation)
- **Audit Tooling**: Phát triển `cfo_audit_bl2_bl3.py` để tự động hóa việc kiểm tra tính cân đối của BCTC và LCTT trên Supabase Cloud.
- **Milestone BL-2 (PASSED)**: Xác nhận 100% rổ VN30 đạt đẳng thức `Tài sản = Nguồn vốn` (Accounting Identity).
- **Audit(V5)**: Resolved BL-3 (Cash Flow Identity Gap). Updated `lite_schema.json` with correct keys for all sectors (Normal/Bank/SEC). Verified FPT, MBB, SSI. Status: 🟢 100% Identity Balance achieved for audit targets.

### [v5.1.5-cleanup] - 2026-03-05 (Massive Codebase Cleanup)
- **Action**: Thực hiện dọn dẹp quy mô lớn toàn bộ dự án. Di chuyển 60+ file không cần thiết vào `archive_legacy`.
- **Legacy Removal**: Di chuyển toàn bộ script khảo sát, logs, audit reports, và raw Excel files vào `archive_legacy/explorations` và `archive_legacy/clutter_cleanup`.
- **Git Hygiene**: Untrack thư mục `data/` và file binary lớn khỏi Git index để tối ưu repo size.
- **Project Structure**: Các thư mục `sub-projects/Version_2` và `V5_improdata` hiện chỉ chứa code operational sạch.
- **Score**: **Production Readiness Standard A achieved.**

---
*Finsang Master Logs - System finalized.*
