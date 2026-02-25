# B.L.A.S.T Pipeline (PDF_TRANS) Project Documentation

Đây là tài liệu tổng hợp dành cho dự án con `PDF_TRANS`, có nhiệm vụ thu thập, bóc tách và kiểm toán Báo cáo tài chính từ Hệ thống HSX/HNX và đẩy vào Database trung gian (Staging). 
Hệ thống được thiết kế theo cấu trúc tách rời (Isolation Integration) để không làm ảnh hưởng tới dữ liệu chính của dự án `Finsang`.

---

## 1. Notes & Architecture (Kiến trúc & Lưu ý)

- **Mục tiêu**: Xây dựng tiến trình thu thập tài liệu tự động BCTC định dạng PDF và trích xuất thành Data API (JSON/SQL).
- **Quy chuẩn B.L.A.S.T**:
  - **Business (Nghiệp vụ CFO)**: Kiểm tra chéo phương trình kế toán (Ví dụ: `Doanh Thu - Giá Vốn = LNTT`).
  - **Logging (Ghi vết)**: Lưu lại toàn bộ mọi quyết định Pass/Fail trong bảng `audit_logs`.
  - **Architecture (Cô lập)**: Hệ thống có Database riêng rẽ (`staging_pdf_trans.db`). Chỉ dữ liệu sạch hoàn toàn (`READY_FOR_SYNC`) mới được cấp phép Sync vào Finsang.
  - **Security (Bảo mật)**: Chống sập hệ thống nhờ ngăn chặn SQL Injection/Dữ liệu rác thông qua môi trường Staging.
  - **Testing**: Tích hợp các bộ mock test dữ liệu.

---

## 2. Implementation Pipeline (Các Module Triển Khai)

Dự án bao gồm 4 công cụ (scripts) hoạt động nối tiếp nhau trong Pipeline:

1. **Network XHR Scraper (`blast_network_crawler.py`)**
   - Nhiệm vụ: Kéo file PDF qua đường mạn network XHR/API (như từ Fireant) thay vì vét HTML tĩnh từ HSX/HNX.
   - Tính năng vượt trội: Tích hợp Exponential Backoff & Retry Logic chống Rate Limit chặn IP.

2. **Fuzzy OCR PDF Ripper (`blast_pdf_ripper.py`)**
   - Nhiệm vụ: Tải file PDF và cắt bảng (Table Extraction).
   - Tính năng vượt trội: Sử dụng thư viện `fitz` (PyMuPDF) để xử lý bảng, và `thefuzz` để vượt qua tình trạng font chữ kiểm toán bị giãn (VD: `K Ế T  Q U Ả`). Hỗ trợ cơ chế Fallback gọi tới hệ thống OCR ở bước tiếp theo nếu BCTC là hình chụp mộc đỏ.

3. **Kế toán trưởng (CFO) Auditor (`blast_auditor.py`)**
   - Nhiệm vụ: Nhận bảng dữ liệu Raw, Normalize các trường ngôn ngữ linh hoạt (Từ Big4) thành Universal Schema chung của Finsang.
   - Thẩm định độ chính xác số liệu bằng phương trình toán học trước khi đẩy sang Database chính.

4. **Staging Database (`staging_db.py`)**
   - Nhiệm vụ: Quản lý hạ tầng dữ liệu SQLite khép kín không phụ thuộc Finsang.
   - Bảng: `raw_reports` (Dữ liệu RAW) & `audit_logs` (Ghi nhận điểm số kiểm toán).

---

## 3. Task Progress & Checklist (Lịch Sử Hoàn Thiện)

> [!NOTE]
> Toàn bộ các công việc dưới đây đã hoàn tất và vượt qua bài Test kiểm định bảo mật hệ thống (CTO Mentor Scan).

- [x] **Phase 1: Architecture Preparation & Isolation (SaaS/Staging Layout)**
  - [x] Create isolated database schema/SQLite for Staging Data (`staging_pdf_trans.db`).
  - [x] Setup `staging_reports` and `audit_logs` tables.
- [x] **Phase 2: Enhanced Scraping & Network API**
  - [x] Implement XHR/Network Interception (e.g., via Fireant network calls instead of pure HTML scraping).
  - [x] Add Retry Logic and Backoff Strategy.
- [x] **Phase 3: Robust PDF Extraction**
  - [x] Integrate Fuzzy Matching for accounting keywords (e.g., `Kết quả kinh doanh`, `K Ế T  Q U Ả`).
  - [x] Implement OCR script fallback for scanned PDFs.
- [x] **Phase 4: Data Normalization & Audit Flow**
  - [x] Map dynamic keywords to Finsang Universal Schema.
  - [x] Apply CFO check: `Revenue - COGS = Gross Profit` và `Assets = Liabilities + Equity`.
  - [x] Push valid records to `READY_FOR_SYNC` status, and invalid records to `PENDING_AUDIT` in Staging DB.
- [x] **Phase 5: CTO Mentorship Verification**
  - [x] Run CTO Audit to score the isolation and security of the new pipeline (Passed 10/10 Isolation).

---

## 4. Integration Guide (Hướng Dẫn Tích Hợp)

Khi Finsang Engine (Production) cần lấy dữ liệu báo cáo tài chính mới:

1. Chạy Scheduler (Cronjob) quét `blast_network_crawler.py` định kỳ hàng ngày.
2. Crawler trả ra `.tmp/link_list.json`, gọi `blast_pdf_ripper.py` bóc tách từng Link PDF và luân chuyển vào Staging DB (Hàm `insert_raw_report`).
3. Chạy lệnh `python blast_auditor.py` để Audit.
4. Core xử lý của Finsang truy cập thẳng vào `staging_pdf_trans.db`, SELECT toàn bộ các bản ghi `WHERE status = 'READY_FOR_SYNC'`, gộp (Merge) vào hệ thống chính, và đánh một dấu flag (VD `SYNCED_TO_CORE`) trên Staging DB.
