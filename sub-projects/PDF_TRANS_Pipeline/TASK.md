# PDF_TRANS — Task Backlog
> Dự án con độc lập với Finsang | Last updated: 2026-02-24

## Mục Tiêu
Tự động hoá việc thu thập BCTC từ PDF gốc HSX/HNX → Staging DB → Finsang Production

---

## ✅ DONE (Session 1 — 2026-02-24)

- [x] Thiết kế kiến trúc B.L.A.S.T Pipeline cho PDF_TRANS
- [x] Tạo `staging_db.py` — SQLite Staging Database độc lập
- [x] Tạo `blast_network_crawler.py` — XHR Crawler với Retry+Backoff
- [x] Tạo `blast_pdf_ripper.py` — PDF Extractor với Fuzzy Match + OCR placeholder
- [x] Tạo `blast_auditor.py` — CFO Audit (phương trình kế toán checksum)
- [x] Viết Workflow `/pdf_trans_workflow` vào `.agent/workflows/`
- [x] Cập nhật `README.md` dự án con
- [x] Crawl thành công link PDF NLG (4Q/2024) từ HSX
- [x] Download PDF NLG + FPT từ `staticfile.hsx.vn`
- [x] Xác nhận: Tất cả PDF trên HSX là **file scan (RICOH printer)** — không có text layer
- [x] Test Fireant API: NLG 4Q + VIC 8Q → 0 sai lệch số liệu so với Fireant Web (dùng làm Benchmark)
- [x] Xác nhận Schema Finsang tương thích với output Long Format từ Fireant API

---

## 🔴 BLOCKED (Cần giải quyết trước)

- [ ] **[CRITICAL] Chọn và cài OCR Engine**
  - Option A: Tesseract + pytesseract + pdf2image + Poppler (free, offline)
  - Option B: Tìm nguồn PDF Digital (VietStock/CafeF)
  - Option C: Google Vision API (trả phí, accuracy tốt nhất)
  - *Quyết định cần từ người dùng*

---

## 🟠 TODO — Blocked on OCR Decision

- [ ] Test OCR với 1 trang BCTC scan → Đánh giá accuracy tiếng Việt
- [ ] Tune Fuzzy Matching threshold trong `blast_pdf_ripper.py` với dữ liệu thực
- [ ] Test `page.find_tables()` / `camelot-py` cho table structure extraction
- [ ] Tích hợp OCR vào `blast_pdf_ripper.py` (thay thế placeholder)
- [ ] End-to-end test: HSX PDF → OCR → Normalize → Audit → Staging DB → So sánh với Fireant Benchmark

---

## 🟡 TODO — Independent Tasks

- [ ] Fix `blast_network_crawler.py`: Gọi 2 API calls để lấy đủ 8 quý từ Fireant
- [ ] Research HNX PDF type (digital hay scan?) — thử 1-2 công ty mid-cap
- [ ] Viết script `run_pipeline.py` để chạy toàn bộ pipeline từ đầu tới cuối bằng 1 lệnh
- [ ] Thêm `SYNCED_TO_CORE` status vào staging_db khi data được approve và merge

---

## 🟢 FUTURE — Integration với Finsang

- [ ] Validate dữ liệu từ Staging đủ chuẩn để INSERT vào `income_statement`, `balance_sheet`, `cash_flow` trong Supabase
- [ ] Viết `sync_to_finsang.py` — script chỉ lấy record `READY_FOR_SYNC` và upsert vào Supabase
- [ ] Viết GitHub Actions workflow riêng cho PDF_TRANS Pipeline (cron job định kỳ)
- [ ] Thêm support cho nhiều mã cổ phiếu (VNM, HPG, MSN, ...) không chỉ NLG

---

## Files Hiện Có Trong `PDF_TRANS_Pipeline/`

| File | Mô tả | Status |
|---|---|---|
| `staging_db.py` | SQLite Staging DB layer | ✅ Tested |
| `blast_network_crawler.py` | XHR Crawler + Retry Logic | ✅ Written |
| `blast_pdf_ripper.py` | PDF Extractor + Fuzzy Match | ⚠️ Needs OCR |
| `blast_auditor.py` | CFO Accounting Equation Audit | ✅ Tested |
| `test_nlg_pipeline.py` | Dry-run NLG via Fireant API | ✅ Tested OK |
| `compare_nlg_sources.py` | Fireant API vs Supabase diff | ✅ Tested OK |
| `test_vic_8q.py` | VIC 8Q via Fireant API | ✅ Tested OK |
| `extract_nlg_pdf.py` | Download + PyMuPDF (NLG) | ❌ Blocked - Scanned |
| `extract_fpt_pdf.py` | Download + PyMuPDF (FPT) | ❌ Blocked - Scanned |
| `debug_pdf.py` | Debug PDF text content | ✅ Tool |
| `check_pdf_types.py` | Check text-layer vs scan | ✅ Tool |
| `README.md` | Tổng quan dự án | ✅ |
| `FINDINGS.md` | Research findings | ✅ |
| `CHALLENGES.md` | Technical challenges log | ✅ |
| `TASK.md` | This file | ✅ |
| `pdfs/NLG/` | 4 PDF files NLG 2024 | ✅ Downloaded |
| `pdfs/FPT/` | 2 PDF files FPT 2024 | ✅ Downloaded |
| `staging_pdf_trans.db` | SQLite Staging DB | ✅ Initialized |
