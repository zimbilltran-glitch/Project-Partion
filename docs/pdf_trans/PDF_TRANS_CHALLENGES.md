# PDF_TRANS — Challenges & Technical Debt Log
> Tương tự `challenges.md` của dự án Finsang chính | CTO Audit: 2026-02-24

---

## Challenge 1: Toàn Bộ BCTC Trên HSX Là File Scan

**Vấn đề:**
PDF BCTC do công ty nộp lên HSX/HNX là bản photocopy có mộc đỏ kiểm toán, được scan bằng máy RICOH MP. File không có text layer — PyMuPDF chỉ đọc được metadata và chữ ký số (~98 chars), không có số liệu tài chính nào.

**Bằng chứng:**
- NLG Q1-Q4/2024 → Creator: `RICOH MP C4504ex` → 0 chars
- FPT Q3-Q4/2024 → Creator: `RICOH MP 4054` → 98 chars (chỉ chữ ký)

**Giải pháp đề xuất:**
- **Option A (Chính):** Cài Tesseract OCR + `pytesseract` + `pdf2image` + Poppler để nhận diện ký tự từ ảnh scan. Cần thêm Vietnamese language pack (`vie.traineddata`) cho Tesseract.
- **Option B (Nhanh):** Dùng nguồn PDF digital từ `vietstock.vn` hoặc `cafef.vn` — các trang này có bản BCTC số hoá (digital-native PDF với text layer đầy đủ).
- **Option C (Cloud):** Dùng Google Cloud Vision API OCR → accuracy cao nhất cho tiếng Việt nhưng tốn chi phí.

**Độ ưu tiên:** 🔴 Critical — Blocking tất cả các bước tiếp theo

---

## Challenge 2: Phạm Vi Lấy Dữ Liệu Fireant API (5 Kỳ / Request)

**Vấn đề:**
Fireant API `full-financial-reports` chỉ trả về **5 kỳ gần nhất** cho mỗi lần gọi, dù truyền `year` và `quarter` bất ký. Để lấy đủ 8 quý (2 năm) cần gọi 2 lần riêng biệt rồi merge kết quả.

**Giải pháp:**
```python
# Gọi 2 lần, 1 cho latest và 1 cho earlier period
url1 = f".../full-financial-reports?type={type_id}&year=2025&quarter=4"
url2 = f".../full-financial-reports?type={type_id}&year=2024&quarter=2"
# Merge + deduplicate theo period key
```

**Độ ưu tiên:** 🟡 Medium — Cần fix trước khi dùng Fireant làm Benchmark Cross-Reference

---

## Challenge 3: Keyword Matching Trong PDF Bị Giãn Cách Font

**Vấn đề (tiềm năng, chưa test được do blocked bởi Challenge 1):**
Do PDF scan → OCR → Text, tên các khoản mục kế toán có thể bị ký tự giãn cách:
- `"K Ế T  Q U Ả  K I N H  D O A N H"` thay vì `"KẾT QUẢ KINH DOANH"`
- OCR thường nhận sai dấu tiếng Việt (ví dụ: `ộ` → `o`, `ế` → `e`)

**Giải pháp:**
- Dùng thư viện `thefuzz` (Fuzzy String Matching) với threshold ≥ 85% để match keyword
- Đã implement sẵn trong `blast_pdf_ripper.py` nhưng chưa test được với file scan thực

**Độ ưu tiên:** 🟠 High — Sẽ cần tune sau khi OCR hoạt động

---

## Challenge 4: Table Structure Extraction Từ PDF

**Vấn đề:**
BCTC Việt Nam có layout phức tạp: bảng ngang nhiều cột, gộp dòng, phân cấp thụt đầu dòng. PyMuPDF `page.find_tables()` hoạt động tốt với digital PDF nhưng chưa được thử với OCR output.

**Giải pháp đề xuất:**
- Sử dụng `camelot-py` hoặc `tabula-py` thay vì `fitz.find_tables()` để extract table structure chính xác hơn
- Hoặc dùng Bounding Box + Row/Column alignment detection từ PyMuPDF

**Độ ưu tiên:** 🟠 High — Xử lý sau khi OCR hoạt động

---

## Challenge 5: Phạm Vi Source Scan Chỉ Đúng Với HSX

**Vấn đề:**
Chưa kiểm tra HNX. Có thể HNX có PDF digital hoặc có cơ chế công bố BCTC khác với HSX.

**Tác vụ cần làm:**
- [ ] Crawl thử HNX cho 1-2 tập đoàn mid-cap để check PDF type
- [ ] Thử `https://hnx.vn/thong-tin-cong-bo-ny-tcph.html` và xem PDF creator

**Độ ưu tiên:** 🟢 Low — Research task

---

## Trạng Thái Kỹ Thuật Nợ (Technical Debt Summary)

| # | Nội dung | Status | Ưu tiên |
|---|---|---|---|
| 1 | OCR Engine cho Scanned PDF | ⏸ Chưa bắt đầu | 🔴 Critical |
| 2 | Fireant 8Q: 2 API calls + merge | ⏸ Chưa bắt đầu | 🟡 Medium |
| 3 | Fuzzy Matching (thefuzz) tune | ⏸ Chưa test thực | 🟠 High |
| 4 | Table Structure Extraction | ⏸ Chưa bắt đầu | 🟠 High |
| 5 | HNX Source Research | ⏸ Chưa bắt đầu | 🟢 Low |
