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
- **Documentation:** Viết mới `Finsang_Team_Guide.md` và tái cấu trúc `README.md` thành điều hướng trung tâm.
- **Security Review:** Rà soát `.gitignore` bảo vệ tuyệt đối file `.env`, `keys.txt` và `data/` Parquet.
- **Legacy Cleanup:** Gắn cờ `[DEPRECATED]` cho `Version_1`, định hướng toàn bộ dev mới sang `Version_2`.
- **Visualization:** Đưa giao diện `streamlit_app.py` ra ngoài root làm Secondary Audit UI dự phòng cho React Dashboard.
- **Bug Fixes:** Cải thiện và tối ưu lại logic load data từ mã hóa Parquet thông qua `pipeline.py` nhằm fix các lỗi đọc sai dòng của thư viện `pyarrow`/`pandas`.
- **UI Research:** Nghiên cứu và phân tách chuẩn bị cho việc tích hợp hệ thống 9 tab từ giao diện mẫu của Simply Wall St.

