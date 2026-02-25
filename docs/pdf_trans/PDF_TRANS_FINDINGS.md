# PDF_TRANS — Findings Report
> CTO Mentor Review | Session: 2026-02-24

## 1. Sourcce Discovery (Phase 1 — Scraper)

### ✅ HSX Static File Server Confirmed
- URL pattern: `https://staticfile.hsx.vn/Uploads/FinancialReport/{company_id}/{filename}.pdf`
- Browser Agent đã crawl thành công trang `https://www.hsx.vn/vi/quan-ly-niem-yet/co-phieu/NLG/2515`
- Tab **"Các báo cáo định kỳ"** chứa danh sách link PDF BCTC theo từng quý

### ✅ NLG PDF Links Collected (4 Quý 2024)
| Kỳ | File | URL |
|---|---|---|
| Q4/2024 | `NLG_Q4_2024.pdf` (13.8 MB) | `staticfile.hsx.vn/Uploads/FinancialReport/336/20250124_...` |
| Q3/2024 | `NLG_Q3_2024.pdf` (10.6 MB) | `staticfile.hsx.vn/Uploads/FinancialReport/336/20241021_...` |
| Q2/2024 | `NLG_Q2_2024.pdf` (3.7 MB) | `staticfile.hsx.vn/Uploads/FinancialReport/336/20240724_...` |
| Q1/2024 | `NLG_Q1_2024.pdf` | `staticfile.hsx.vn/Uploads/FinancialReport/336/20240426_...` |

### ✅ FPT PDF Links Collected (Cross-check)
| Kỳ | File |
|---|---|
| Q4/2024 | `staticfile.hsx.vn/Uploads/FinancialReport/13/20250124_...FPT...Q4...pdf` |
| Q3/2024 | `staticfile.hsx.vn/Uploads/FinancialReport/13/20241024_...FPT...Q3...pdf` |

---

## 2. PDF Type Analysis (Phase 2 — Extractor)

### ❌ CRITICAL FINDING: All HSX PDFs Are Scanned Images

| Company | File | Creator (Printer) | Text Layer | Type |
|---|---|---|---|---|
| NLG | Q1-Q4/2024 | **RICOH MP C4504ex** | 0 chars | 📷 Scanned |
| FPT | Q3-Q4/2024 | **RICOH MP 4054** | 98 chars (chữ ký) | 📷 Scanned |

**Root Cause:** Công ty VN nộp BCTC lên sàn là bản scan mộc đỏ kiểm toán (hardcopy → photo → PDF). Không có text layer để PyMuPDF kéo ra.

### ✅ Fireant API — Validated Benchmark Source
- Bearer Token có thể bắt qua Playwright XHR interception từ trang `fireant.vn/ma-chung-khoan/{symbol}/tinh-hinh-tai-chinh`
- API endpoint: `https://restv2.fireant.vn/symbols/{symbol}/full-financial-reports?type={1|2|3|4}&year={y}&quarter={q}`
- Type IDs: `1=CDKT`, `2=KQKD`, `3=LCTT_TT`, `4=LCTT_GT`
- **Kết quả**: Số liệu khớp 100% với Fireant Web UI (NLG 4 quý, VIC 8 quý — 0 sai lệch)
- **Giới hạn**: API chỉ trả 5 kỳ gần nhất mỗi lần gọi. Cần 2 calls để phủ 8 quý.
- **Quan trọng**: Fireant API là **nguồn Benchmark Cross-Reference**, NOT nguồn chính của PDF_TRANS

---

## 3. Staging Database Architecture (Phase 4)

### ✅ SQLite Staging DB hoạt động
- File: `PDF_TRANS_Pipeline/staging_pdf_trans.db`
- Bảng: `raw_reports` (PENDING_AUDIT → READY_FOR_SYNC → REJECTED)
- Bảng: `audit_logs` (CFO checksum kết quả)
- Test Audit PASSED: Record VNM mock data thoả phương trình `Doanh thu - Giá vốn = LNTT`

### ✅ Finsang Schema Compatibility Confirmed
- DB schema đích: Long Format `(stock_name, period, item_id, item, levels, row_number, value, source)`
- Data từ Fireant API (sau normalize) **tương thích hoàn toàn** với `income_statement`, `balance_sheet`, `cash_flow` trong Supabase

---

## 4. Tóm Tắt Kiến Trúc B.L.A.S.T Hiện Tại

```
HSX/HNX → scanned PDF
              ↓
         [BLOCKED: No text layer → must use OCR]
              ↓
         OCR Engine (Tesseract/Google Vision)
              ↓
         blast_pdf_ripper.py (Fuzzy Match keywords)
              ↓
         blast_auditor.py (CFO Validate)
              ↓
         staging_pdf_trans.db (PENDING_AUDIT)
              ↓
         Admin Review → READY_FOR_SYNC
              ↓
         Finsang Production DB (Supabase)
```

**Alternative (Parallel Track):**
```
Fireant API → blast_network_crawler.py → Normalize → Audit → Staging → Sync
```
