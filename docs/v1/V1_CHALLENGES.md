# Sổ tay Kỹ thuật: Khó khăn & Giải pháp (Challenges Log)

Tài liệu này ghi nhận các vấn đề kỹ thuật (technical stucks), lỗi (bugs) gặp phải trong quá trình phát triển dự án chứng khoán B.L.A.S.T, cùng phương án đã giải quyết.

## 1. Nguồn Dữ liệu & Handshake (Phase L)
**Vấn đề:** 
Thư viện `vnstock3` (phiên bản fork `vnstock3_learn`) báo lỗi "Forbidden-ban" khi khởi tạo. Sau khi chuyển sang cài package gốc `vnstock` chuẩn thì lại gặp lỗi "Cannot import name 'FinancialReport'".
**Nguyên nhân:**
Thư viện `vnstock` nguyên bản đã chia nhỏ hệ sinh thái, module `FinancialReport` không có sẵn trong thư viện chính nếu gọi sai cấu trúc, hoặc các hàm cũ đã deprecate (không còn hỗ trợ). API Endpoint của KBSV cũng ẩn giấu các Params.
**Giải pháp:**
- Dùng chức năng Reverse-engineering (Dịch ngược) từ file `Walkthrough` để lôi thẳng cấu trúc URL API của KB Securities: `https://kbbuddywts.kbsec.com.vn/sas/kbsv-stock-data-store/stock/finance-info/...`
- Gọi API trực tiếp bằng thư viện `requests` kèm đủ Header (`User-Agent`) và Query Parameters (`termtype`, `unit`, `languageid`) thay vì lệ thuộc vào object `FinancialReport` của `vnstock`. 
- Đối với dữ liệu OHLCV, tiếp tục sử dụng object `Quote` của `vnstock` vì endpoint này của KBS cấu trúc đơn giản, ít lỗi và hỗ trợ `api_key` VIP.

## 2. Thiết kế Cơ sở dữ liệu Báo cáo Tài chính (Phase A)
**Vấn đề:**
Excel chứa BCTC của User cung cấp là Bảng Ngang (WIDE table - mỗi Quý/Năm là một cột). Nếu thiết kế CSDL SQL (Supabase) lưu nguyên dạng bảng ngang này, cấu trúc sẽ bị "cứng", mỗi khi có một quý mới trôi qua, ta phải chạy lệnh `ALTER TABLE` thêm cột thủ công, rất dễ gây lỗi hệ thống.
**Giải pháp:**
- Bẻ CSDL trên Supabase thành định dạng Dọc (LONG Data) `financial_reports`. Mỗi giá trị của một hạng mục trong 1 quý sẽ là 1 HÀNG độc lập (gồm cột `period`, `item_id`, `value`).
- Tại Phase S (Presentation), dùng SQL Pivot (hàm `jsonb_object_agg` của PostgreSQL) để nhóm (Group By) các khoản mục lại, "gói" tất cả các quý thành 1 cục JSON. Frontend dựa vào cục JSON này vẽ bảng chéo y hệt Excel mà không cần đổi cấu trúc DB bao giờ.

## 3. Kiến trúc Giao diện Frontend (Phase S)
**Vấn đề:**
User cung cấp ảnh mẫu `sample_group_fin.png` (bảng Excel thuần) nhưng lại yêu cầu giao diện Website phải giống phong cách của `Simplize` (Dark Theme chuyên nghiệp, gọn gàng, có bar chart mini nhúng trong bảng). Đồng thời, User yêu cầu công nghệ Frontend phải trực quan, dễ maintain (dễ bảo trì) cho người mới bắt đầu lập trình.
**Giải pháp:**
- **Công nghệ Frontend**: Loại bỏ TailwindCSS (do cú pháp dài dòng rối mắt người mới). Sử dụng **Vite + React + Vanilla CSS (CSS thuần)**. Cách này giúp code trong suốt, file `App.jsx` chỉ chứa logic lấy dữ liệu (Supabase), file `App.css` độc lập quản lý màu sắc Dark Theme và Layout (Grid/Flexbox/Sticky Header).
- **Trình bày Bảng (Data Table)**:
  - Khởi tạo CSS Lock cho cột đầu tiên (Cột Khoản mục) và dòng tiêu đề (Dòng Thời gian) bằng thuộc tính `position: sticky`. Mục đích là khi Data trải dài 5-10 năm theo chiều ngang, người dùng kéo sang phải vẫn giữ được Tên khoản mục. (Tránh lỗi trôi header kinh điển của HTML Table thuần).
  - Tự động lấy các key JSONB từ Supabase (`2024-Q1`, `2024-Q2`,...) sinh ra các cột động `<th>` mà không phải hardcode. Phân cấp (levels) thò thụt dòng theo biến `levels` trong DB thay vì chèn space thủ công.
  - Tích hợp 1 Component `MiniBarChart` tự vẽ các div siêu nhỏ với chiều cao tính theo % giá trị Max của hàng đó, đáp ứng được nét đặc sắc của Theme Simplize.

## 4. Kiểm định Chất lượng Dữ liệu & Mật độ Dữ liệu (Phase D)
**Vấn đề:**
Ở giai đoạn đầu, hệ thống chỉ lấy dữ liệu từ một nguồn duy nhất (API của KBSV). Sau khi kiểm duyệt chéo với template trên Google Sheet, phát hiện API trả về dữ liệu thưa (Sparse Data) - nghĩa là KBSV tự động "cắt bỏ" hoặc "ẩn đi" hơn 60 dòng chỉ tiêu nếu công ty đó không có phát sinh (giá trị = 0). 
Hậu quả là Database lưu y nguyên cấu trúc thưa thớt này. Về lâu dài, khi Model tính toán của Data Scientist chạy hoặc khi xây dựng Dashboard, hệ thống chắc chắn sẽ bị sập vì lỗi `KeyError` (không tìm thấy chỉ tiêu tương ứng để tính toán tỷ số tài chính). Làm sao để vừa lấy đúng, vừa đảm bảo lưu trữ chuẩn mật độ mà không sai lệch bản chất kế toán?

**Giải pháp:**
Việc này đòi hỏi sự phối hợp khắt khe của 4 bộ kỹ năng liên hoàn:
- **Tạo Khuôn Cố Định (Master Template):** Áp dụng kỹ năng `@database-design`, tạo một bảng `tt200_coa` chứa toàn bộ các chỉ tiêu theo chuẩn mực Kế toán TT200. Data Pipeline (`fetch_financials.py`) bị buộc phải Left Join dữ liệu API rách nát vào cái khuôn này. Nơi nào API thiếu số, gán mặc định `value = 0` thay vì bỏ trống dòng. Nhờ đó biến đổi Sparse Data thành Dense Data (Dữ liệu đặc).
- **Đối soát Đa Nguồn (Multi-Source Benchmarking):** Rút kinh nghiệm từ tính mong manh của một nguồn API duy nhất, hệ thống thiết kế thêm cột `source` cho tất cả các bảng gốc. Xây dựng thêm ba bảng Benchmark riêng biệt (`income_statement_benchmark`, v.v.).
- **Tự động hoá Đối soát & Thách thức Web Scraping:** Dùng kỹ năng `@autonomous-web-scraper` (chạy script `Crawl4Ai` ưu tiên số 1 để tránh tốn Token) và `@firecrawl-scraper` làm phương án dự phòng để cào dữ liệu BCTC hoàn chỉnh từ nguồn cực kỳ uy tín là **Simplize.vn** (nếu lỗi sẽ nhảy sang **finance.vietstock.vn**). 
  - **Vấn đề phát sinh (Scraping Blockers):** Quá trình cào thực tế cho thấy `Crawl4Ai` bị block hoặc không render được các table SPA phức tạp trên Simplize, dẫn đến script tự động fallback sang `FireCrawl`. 
  - **Rủi ro chi phí (Token Limits):** Do phải sử dụng `FireCrawl` liên tục, rủi ro tiêu hao Token rất nhanh. Nếu mở rộng cào dữ liệu cho toàn bộ VN30 hoặc thị trường, quota của API này chắc chắn không đủ. 
  - **Hướng giải quyết tương lai:** Nhận diện được điểm nghẽn này, tương lai cần bắt giải pháp: (1) Thay vì cào HTML/Markdown, sử dụng Reverse Engineering API nội bộ của Simplize y như cách đã làm với KBSV; hoặc (2) Nâng cấp `Crawl4Ai` với các thiết lập Puppeteer/Playwright Stealth tinh vi hơn (đợi Render JS hoàn chỉnh) để tự chủ 100% việc lấy dữ liệu mà không phụ thuộc 3rd Party API.
- **Kiểm toán CFO (Data Audit):** Trước khi gán mác "Chuẩn" cho dữ liệu vừa cào, kỹ năng `@professional-cfo-analyst` sẽ được kích hoạt để chạy checksum định lý Kế toán (Ví dụ: `Tổng Tài Sản = Tổng Nguồn Vốn`). Chỉ khi Audit PASSED, script `reconcile_simplize.py` mới đem đi quét Diff với Database hiện tại. Đảm bảo 100% không lọt rác vào Production.

## 5. Nợ Kỹ thuật & Khắc phục từ CTO Audit (Phase T)
**Vấn đề:**
Sau khi quét dự án, Giám đốc Kỹ thuật (`@cto-mentor-supervisor`) đã chỉ ra 3 rủi ro thiết kế cấp bách mang tính hệ thống (Technical Debt):
1. **Rủi ro Infinite Loop ở hàm đệ quy `Levels`:** Hiện tại hàm `build_tree` dựa vào `ParentReportNormID` chưa có Unit Tests. Nếu API trả về cấu trúc vòng rỗng hoặc móc vòng, pipeline có thể bị treo vĩnh viễn.
2. **Thiếu Tự Động Hóa (Decoupled Scripts):** Các script ETL Python đang phải chạy rời rạc. Khi list mã lệnh phình lên 1,000 mã, không thể gọi script bằng tay.
3. **Chi phí FireCrawl bùng nổ:** Việc dự phòng bằng Firecrawl (để phá Block JS trên Simplize) sẽ làm cạn kiệt Token ngân sách rất nhanh.

**Giải pháp (Đã hoàn tất):**
- **Giải quyết Rủi ro 1 (Testing):** Tích hợp `pytest` vào folder `tests/test_fetch_financials.py`, tạo mock JSON rác (vòng lặp vô tận) để bắn vào hàm đệ quy của `fetch_financials.py`. **PASS**: Script phát hiện đứt gãy và throw Exception/trả về đúng levels mà không bị Loop vô tận.
- **Giải quyết Rủi ro 2 (Orchestration):** Viết tệp `orchestrator.py` đóng vai trò là Central Worker DAG. Khi kích hoạt bằng 1 lệnh duy nhất (`python orchestrator.py --symbol NLG`), toàn bộ 5 pipeline (OHLCV -> Dense Merge -> Ratios -> Web Scraper -> CFO Audit) sẽ chạy ngầm nối đuôi nhau hoàn toàn tự động.
- **Giải quyết Rủi ro 3 (Stealth Bot):** Cài đặt engine Playwright `crawl4ai` và kích hoạt cờ `magic=True` (Stealth Mode). Crawler đã xé toạc lớp bảo vệ Cloudflare/JS của Simplize, tự động load Table JS và cào 327 dòng dữ liệu cực ngọt ngào mà không tốn 1 đồng Token của API FireCrawl dự trù. 

---
*(CTO Audit Nợ Kỹ Thuật Đã Được Thanh Toán Hoàn Toàn)*

## 6. Lỗi Dữ Liệu Fireant & Thuật Toán Matching (Phase V2)

### Vấn đề 1: Trùng Lặp Ngữ Nghĩa (Semantic Collision) — mất 98% dữ liệu CDKT

**Triệu chứng:**
Sau lần chạy đầu tiên của `fetch_fireant.py`, SQL kiểm tra trả về:
- `income_statement`: 110 dòng ✅ (đúng kỳ vọng)
- `balance_sheet`: **5 dòng** ❌ (kỳ vọng: 360 dòng)
- `cash_flow`: **0 dòng** ❌

**Nguyên nhân gốc rễ:**
API `full-financial-reports` của Fireant trả về một mảng JSON phẳng (flat array) trong đó nhiều khoản mục sử dụng **cùng một tên chính xác** để diễn đạt các dòng thuộc các phân lớp khác nhau. Ví dụ điển hình:

| Thứ tự trong JSON | Tên khoản mục | Thuộc phân lớp |
|---|---|---|
| #12 | `- Nguyên giá` | TSCĐ Hữu hình |
| #19 | `- Nguyên giá` | TSCĐ Vô hình |
| #26 | `- Nguyên giá` | BĐS Đầu tư |

Code ban đầu xây dựng một Python Dictionary (Hashmap) từ `tt200_coa`:
```python
coa_lookup = {}
for c in coa_db:
    key = str(c["item"]).strip().lower()
    coa_lookup[key] = c  # ❌ key thứ 2 ghi đè key thứ 1
```
Kết quả: Hashmap chỉ giữ lại bản ghi *cuối cùng* của mỗi tên trùng. Khi vòng lặp JSON lên tới `- Nguyên giá` lần 2 và 3, chúng không match được dòng COA tương ứng (dòng thứ 1 đã bị ghi đè), nên bị bỏ qua (`continue`). Đây là lý do chỉ có **5/360 dòng** được map thành công — tất cả 5 dòng đó là các khoản mục **tên duy nhất** trong CDKT như `Lợi nhuận sau thuế chưa phân phối lũy kế đến cuối kỳ trước`.

**Giải pháp — Ordered Sliding Window Matching:**
Thay vì tra cứu ngẫu nhiên qua Hashmap, chuyển sang thuật toán tuyến tính có hướng (forward-only linear scan) với 3 bước:

1. **Sắp xếp template:** Tải `tt200_coa` từ Supabase và sort theo `row_number` tăng dần, đảm bảo thứ tự khớp với thứ tự xuất hiện trên báo cáo Fireant.
2. **Con trỏ tịnh tiến (`db_search_ptr`):** Duy trì một con trỏ nguyên bắt đầu từ `0`. Với mỗi dòng JSON từ Fireant, chỉ tìm kiếm từ vị trí con trỏ **trở về sau** — không cho phép quay lui.
3. **Hai lần quét (Two-Pass):**
   - *Pass 1 – Exact Match:* So sánh `search_key == db_item_name` (sau khi normalize: `.lower()`, bỏ `(*)` và khoảng trắng thừa). Nếu khớp, lưu COA và tăng con trỏ lên 1.
   - *Pass 2 – Fuzzy Substring Match:* Nếu Pass 1 không khớp, quét tiếp và kiểm tra `search_key in db_item_name or db_item_name in search_key`. Dùng làm lưới an toàn cho các dòng bị viết tắt nhẹ.

**Kết quả:** `balance_sheet` tăng từ **5 → 360 dòng** (đạt 100% mật độ dữ liệu).

---

### Vấn đề 2: Lỗi 0 Dòng trên Báo Cáo LCTT (Lưu Chuyển Tiền Tệ)

**Triệu chứng:**
Sau khi fix Vấn đề 1, LCTT vẫn trả về 0 dòng dù pipeline đã chạy xong không có lỗi nào.

**Quá trình điều tra:**

*Giả thuyết sai ban đầu:* Fireant dùng endpoint khác (`financial-reports`, dạng Matrix) cho LCTT thay vì `full-financial-reports` (dạng Tree). Triển khai cả hai nhánh API song song làm code trở nên phức tạp và phát sinh lỗi `TypeError: 'NoneType' object is not iterable` ngay khi chạy. Tốn nhiều vòng debugging.

*Kiểm tra thực nghiệm:* Chạy `probe_fireant.py` với Playwright để click vật lý vào tab "Lưu chuyển tiền tệ" hòng bắt XHR request. Thất bại do Fireant thay đổi cấu trúc DOM — locator `text=Lưu chuyển tiền tệ` bị Timeout 5000ms.

*Probe trực tiếp qua Python `requests`:* Bắn thẳng request tới:
```
GET https://restv2.fireant.vn/symbols/NLG/full-financial-reports?type=3&year=2024&quarter=4
GET https://restv2.fireant.vn/symbols/NLG/full-financial-reports?type=4&year=2024&quarter=4
```
Kết quả: **cả 2 endpoint đều trả về dữ liệu LCTT chuẩn cấu trúc Tree** (không phải Matrix). API không phải là vấn đề.

**Nguyên nhân gốc rễ thực sự:**
Script Python có đoạn code alias cũ:
```python
if report_type_str == "LCTT_TT": report_type_query = "LCTT_TRUC_TIEP"
if report_type_str == "LCTT_GT": report_type_query = "LCTT_GIAN_TIEP"
```
Nhưng khi query `tt200_coa` với `report_type = 'LCTT_GIAN_TIEP'` thì Supabase trả về **mảng rỗng** (`[]`), vì bảng `tt200_coa` được seed theo chuẩn mới với giá trị `LCTT_GT` (không phải `LCTT_GIAN_TIEP`). Hệ quả: `coa_db` rỗng, vòng lặp sliding window không có gì để match, toàn bộ 0 dòng insert.

**Giải pháp:**
Xóa 2 dòng alias hardcode. Script truyền thẳng `LCTT_TT` và `LCTT_GT` vào query — khớp chính xác với giá trị trong `tt200_coa`.

**Kết quả:** `cash_flow` tăng từ **0 → 255 dòng** (LCTT Trực tiếp + Gián tiếp × 5 kỳ).

**Tổng kết Phase V2.1 — Final Metrics:**
| Bảng | Trước fix | Sau fix | Mật độ |
|---|---|---|---|
| `income_statement` | 110 | 110 | ✅ 100% |
| `balance_sheet` | 5 | 360 | ✅ 100% |
| `cash_flow` | 0 | 255 | ✅ 100% |



---

## 7. UI Portal — Dòng Trùng Lặp & Source Filter (Phase V2-UI)

**Vấn đề:** Portal hiển thị mỗi dòng CDKT/KQKD/LCTT hai lần — một từ KBSV, một từ FIREANT.

**Nguyên nhân:** SQL views (alance_sheet_wide...) thiếu WHERE source = 'FIREANT', GROUP BY ra 2 bản ghi riêng cho cùng item_id.

**Giải pháp:** Thêm WHERE source = 'FIREANT' vào cả 3 wide views qua Supabase migration.

**Kết quả:** Dòng trùng biến mất hoàn toàn.

---

## 8. UI Portal — Minibar Chart & 8-Quarter Display (Phase V2-UI)

**Vấn đề:** (a) Minibar sort sai thứ tự thời gian; (b) Số âm render lung tung không có baseline; (c) Portal chỉ hiện 5 quý; (d) Số dùng dấu chấm thay vì dấu phẩy.

**Giải pháp:**
- **(a)** periods sort Z→A (newest-first) → chartVals = periods.map(...) là newest-first tự nhiên.
- **(b)** Simplize-style: .bar-pos-area (flex-end, grow UP) + .bar-neg-area (flex-start, grow DOWN). Xanh dương lên, đỏ tụt xuống.
- **(c)** etch_fireant.py cập nhật year=2025, quarter=4 → Fireant API trả về 8 quý tự động.
- **(d)** Intl.NumberFormat('en-US') → 27,549,220 (comma separator).
- **(e)** Period normalization: Q4/2025 → 2025-Q4 internally; hiển thị Q4/2025.
- **(f)** Auto-expand levels <= 1 khi React load.

**Kết quả:** CDKT/KQKD/LCTT hiển thị đúng 8 quý, số đúng format, minibar chính xác.

---

## 9. Security — Sensitive Files Chưa Gitignored (Phase SEC)

**Vấn đề:** CTO Security Audit phát hiện keys.txt, ireant_network.json (112KB), ireant_network.log, lctt*.json, cdkt.txt, kbsv_items.txt chưa có trong .gitignore. Các file này chứa intercepted Bearer token URLs và raw API payloads.

**Giải pháp (OWASP A02 – Cryptographic Failures):**
`
keys.txt | fireant_network.json | fireant_network.log
fireant_unmatched.log | lctt*.json | cdkt.txt
kbsv_items.txt | *.log | .venv/
`

**Checklist:** supabaseClient.js → VITE env vars ✅ | Python .env → gitignored ✅ | etch_fireant.py Bearer token → runtime-only (Playwright intercept, never stored in code) ✅
