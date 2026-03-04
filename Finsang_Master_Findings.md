# Finsang Master Findings Report

> **Audit Date:** 2026-03-01 | **Auditor:** Antigravity Agent
> **Scope:** Full project review — Backend, Frontend, Data, Security, Architecture

---

## 📌 Mục đích Audit

Rà soát toàn diện dự án Finsang nhằm:
1. Kiểm tra tiến độ theo 5 mục tiêu gốc (BCTC, Multi-source, Phân ngành, Ngành-specific, Web)
2. Phát hiện bugs, rủi ro bảo mật, khoảng trống chức năng
3. Lập danh sách công việc chính xác cho giai đoạn tiếp theo

---

## F-001: Bug `load_tab_from_supabase()` — Biến chưa định nghĩa

| Field | Value |
|---|---|
| **Severity** | 🔴 CRITICAL |
| **File** | `sub-projects/Version_2/pipeline.py` line 392 |
| **Impact** | Crash toàn bộ luồng CSTC metrics (metrics.py import hàm này) |

**Chi tiết:**
```python
# Line 392 — biến sheet_upper KHÔNG TỒN TẠI
ordered_fields = [f for f in schema_raw["fields"] if f["sheet"].upper() == sheet_upper]
#                                                                          ^^^^^^^^^^^
# Phải sửa thành: sheet.upper()
```

**Root Cause:** Khi refactor từ `load_tab()` (local Parquet) sang `load_tab_from_supabase()`, biến `sheet` parameter không được đổi tên thành `sheet_upper`.

**Fix:** Thay `sheet_upper` → `sheet.upper()` tại line 392.

---

## F-002: Duplicate Encryption Key trong `.env`

| Field | Value |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **File** | `.env` lines 6 + 8 |
| **Impact** | Key đầu tiên bị override, có thể gây mất dữ liệu nếu Parquet cũ dùng key khác |

**Chi tiết:**
```env
FINSANG_ENCRYPTION_KEY=3OQ2AZnwS69CJxZfDQamVfbfaWNz6AjfDux3MM4FrPA=   ← bị override
FINSANG_ENCRYPTION_KEY=LNMqLeTwoBfGtVyB9LB6tJ_wQRThQb52rI7Ft8R7Q1E=   ← key đang dùng
```

**Nguồn gốc key:** Đây là **Fernet AES-128 key** tự generate bởi `security.py > Fernet.generate_key()`, dùng để mã hóa file Parquet tại local. **KHÔNG PHẢI** key Supabase.

**Root Cause:** Hàm `add_key_to_env()` trong `security.py` được gọi 2 lần → append thêm key mới thay vì update.

**Fix:** Xóa dòng key cũ (line 6), giữ key cuối cùng. Verify Parquet files đọc được với key hiện tại.

---

## F-003: Frontend hoàn toàn không nhận biết nhóm ngành (Sector-blind)

| Field | Value |
|---|---|
| **Severity** | 🔴 CRITICAL |
| **File** | `frontend/src/App.jsx` |
| **Impact** | Ticker Ngân hàng (MBB, VCB...) và Chứng khoán (SSI, VND...) hiển thị sai/trống |

**Chi tiết:**
- `App.jsx` luôn query cùng 4 table views (`balance_sheet_wide`, `income_statement_wide`, `cash_flow_wide`, `financial_ratios_wide`) cho tất cả ticker
- Không có logic phân loại sector → không đổi tabs hay fields theo nhóm ngành
- Kết quả: Bank tickers hiển thị hàng trống vì dùng field schema của Phi Tài Chính

**Backend đã sẵn sàng:**
- `pipeline.py` đã có `get_sheets_for_ticker()` routing đúng sector
- `golden_schema.json` đã có 10 sheets (3 sector × 3 BCTC + NOTE)
- `metrics.py` đã có `calc_bank_metrics()`, `calc_sec_metrics()`, `calc_normal_metrics()`

**Thiếu:** Frontend cần phát hiện sector của ticker → hiển thị đúng bộ đầu mục.

---

## F-004: Sector classification đang hardcode

| Field | Value |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **File** | `pipeline.py` lines 62-63, `metrics.py` lines 10-11 |
| **Impact** | Mở rộng ra ngoài VN30 sẽ phải sửa code thủ công |

**Chi tiết:**
```python
# Hardcoded tại 2 file khác nhau (không DRY)
BANK_TICKERS = {"ACB", "BID", "CTG", "HDB", "MBB", "SHB", "SSB", "STB", "TCB", "TPB", "VCB", "VIB", "VPB"}
SEC_TICKERS = {"SSI", "HCM", "VCI", "VND"}
```

**Giải pháp đề xuất:** Tạo bảng `companies` trên Supabase lưu sector metadata, hoặc fetch từ Vietcap API.

---

## F-005: Supabase RLS bị disable trên các bảng chính

| Field | Value |
|---|---|
| **Severity** | 🟡 MEDIUM (sẽ là CRITICAL khi deploy) |
| **Tables** | `balance_sheet`, `income_statement`, `cash_flow`, `financial_ratios` |
| **Impact** | Bất kỳ ai có anon key đều read/write được toàn bộ data |

**Chi tiết từ Supabase:**
- `balance_sheet` → `rls_enabled: false`
- `income_statement` → `rls_enabled: false`
- `cash_flow` → `rls_enabled: false`
- `financial_ratios` → `rls_enabled: false`

**Lưu ý:** Các bảng legacy (`financial_reports`, `tt200_coa`, `pipeline_runs`) lại có RLS = true.

**Fix:** Enable RLS + tạo policy cho phép:
- `anon` → SELECT only (frontend đọc)
- `service_role` → INSERT/UPDATE/DELETE (pipeline ghi)

---

## F-006: Fireant pipeline tồn tại nhưng chưa tích hợp V2

| Field | Value |
|---|---|
| **Severity** | 🟢 LOW (enhancement) |
| **Files** | `tools/fetch_fireant.py`, `tools/fireant_mappings.py`, `tools/probe_fireant.py` |
| **Impact** | Không có nguồn dữ liệu thứ hai để đối chiếu |

**Chi tiết:**
Pipeline Fireant đã có khá hoàn chỉnh gồm:
- Bearer token hijack qua Playwright
- API mapping cho CDKT/KQKD/LCTT
- Ordered Sliding Window matching algorithm
- Upsert trực tiếp lên Supabase

**Nhưng chưa tích hợp V2 vì:**
1. Dùng luồng riêng (`tt200_coa` table) thay vì V2 Provider pattern
2. Period format khác: `2025-Q4` (Fireant) vs `Q4/2025` (Vietcap V2)
3. Chưa có `FireantProvider(BaseProvider)` class
4. Token hijack qua Playwright → dễ hỏng khi Fireant đổi frontend

---

## F-007: Chỉ số tài chính chưa tính đúng theo nhóm ngành trên web

| Field | Value |
|---|---|
| **Severity** | 🔴 HIGH |
| **File** | `metrics.py` (backend OK), `App.jsx` (frontend thiếu) |
| **Impact** | Tab CSTC hiển thị metrics sai cho Banks/Securities |

**Chi tiết:**
- Backend `metrics.py` đã có 3 bộ calculator riêng biệt (Normal, Bank, Securities)
- Nhưng `sync_supabase.py` ghi tất cả vào cùng `financial_ratios` table
- Frontend không có logic phân biệt → hiển thị metrics kiểu gì cũng chung 1 bộ

---

## F-008: Data trên Supabase đã đầy đủ VN30

| Field | Value |
|---|---|
| **Severity** | 🟢 INFO (Cập nhật lại đánh giá) |
| **Source** | `vn30_enrichment.py` |

**Chi tiết xác nhận từ query SQL trực tiếp:**
- `balance_sheet`: 31 tickers × ~3,880 rows = 119,683 rows (source: vietcap)
- `income_statement`: 31 tickers × ~960 rows = 29,712 rows
- `cash_flow`: 31 tickers × ~1,635 rows = 50,717 rows
- `financial_ratios`: 6,599 rows (source: CFO_CALC_V2)

→ Script `vn30_enrichment.py` đã chạy thành công cho toàn bộ VN30 + VHC.

---

## F-009: Cập nhật dữ liệu theo quý, không cần hằng ngày

| Field | Value |
|---|---|
| **Severity** | 🟢 INFO (Design decision) |
| **Owner** | Product Owner |

**Decision:** BCTC chỉ cần cập nhật theo **quý** (khi công ty nộp báo cáo). Không cần scheduler chạy hằng ngày. Khi quý mới đến, chỉ cần chạy `run_all.py` hoặc `vn30_enrichment.py` một lần.

---

## F-011: Thiếu dữ liệu do cấu trúc BCTC ghi chép khác nhau (Nature-based Missing)

| Field | Value |
|---|---|
| **Severity** | � HIGH |
| **File** | `sub-projects/Version_2/metrics.py` |
| **Impact** | Các trường như "Vốn góp", "Tiền", "Lãi cổ đông mẹ" bị `null` trên UI do không khớp mapping chuẩn |

**Chi tiết:**
- Vietcap API trả về các dòng BCTC tuân theo cách báo cáo của từng công ty. Ví dụ FPT không có dòng "Vốn góp" hay "Lãi chưa phân phối" tổng, mà tách lẻ hoặc gộp vào mục khác.
- Mapping 1-1 bằng ID mảng bị lỗi `null` và gây crash numpy (`ndarray not callable`) khi đẩy lên DB Supabase.

**Giải pháp đã triển khai (CFO Nature-based Mapping):**
- Đã can thiệp vào `metrics.py` (`calc_normal_metrics`, `calc_bank_metrics`, `calc_sec_metrics`).
- Sử dụng quy tắc kế toán để tạo fallbacks: 
  - `[Tiền và TĐ tiền] = [Tiền] + [Các khoản tương đương tiền]`
  - `[Lãi ròng CĐ Công ty mẹ] = Fallback về [LNST TNDN]` nếu không có lợi ích thiểu số.
- Chạy lại toàn bộ dữ liệu 31 mã VN30 (lệnh `sync_supabase.py --all`) và xác nhận 100% lên số chuẩn xác trên Vite Frontend.

---

## F-012: Mã nguồn gọi API (requests) không có Timeout

| Field | Value |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Files** | `tools/explore_kbs.py`, `fetch_financials.py`, `fetch_fireant.py`, `scrape_simplize.py`, `check_vc_js.py` |
| **Impact** | Nếu server đích treo không phản hồi, toàn bộ pipeline sẽ treo vĩnh viễn (hanging) thay vì throw TimeoutError. |

**Chi tiết:**
- Quét tĩnh SAST bằng `Bandit` báo cáo nhiều kết quả: "Call to requests without timeout".
- Các file crawl data/api đang sử dụng `requests.get(url)` mà không có tham số `timeout=`.

**Giải pháp:**
- Cập nhật toàn bộ các call `requests.get`/`post` có thêm tham số `timeout=10` (hoặc cấu hình được).
- Xây dựng retry mechanism hoặc error handling để log lại các requests quá hạn.

---

---

## F-013: Kiến trúc biểu đồ thiếu tính mở rộng cho Data Phức tạp

| Field | Value |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Component** | `frontend/src/App.jsx` & V3 Data Hooks |
| **Resolution** | Đang xử lý tại Phase 4.0 (`V4_Chart_Improve`) |

**Chi tiết:**
- Việc sử dụng Pure SVG ở V3.0 tốt cho bundle size nhưng bộc lộ điểm yếu khi cần dựng biểu đồ phức tạp như Cột ghép (Grouped Bar), Miền (Stacked Area) và 2 trục tung (Dual Axis).
- Thiếu các Tooltip tương tác có Crosshair, gây khó khăn cho CFO nhìn data chính xác.

**Hành động cải thiện:**
- Triển khai Sub-project `V4_Chart_Improve` với thư viện `recharts`.
- Parser lại CĐKT và KQKD `_wide` data thành dạng timeseries arrays.

---

## F-014: Tái cấu trúc Source Code & Audit Security (CTO Level)

| Field | Value |
|---|---|
| **Severity** | 🟢 INFO (Hoàn thành) |
| **Component** | Toàn bộ dự án |
| **Action** | Dọn dẹp, lưu trữ File rác và Kiểm tra bảo mật |

**Chi tiết Audit & Hành động:**
- **Codebase De-clutter:** 
  - Đã di chuyển toàn bộ thư mục `sub-projects/Version_1` (mã nguồn cũ dựa trên Playwright) và thư mục `tools` (các script cào dữ liệu thô, không theo chuẩn B.L.A.S.T) vào thư mục `archive_legacy/`.
  - Quét thư mục `Version_2` và phát hiện một loạt các file dump `search_raw_*.json`, `_verify_out.txt`, và các script test `check_*.py`, `test_*.py`. Toàn bộ đã được đưa vào `archive_legacy/explorations`. Hiện tại `Version_2` chỉ chứa mã nguồn Core Engine.
- **Security Check:**
  - Kiểm tra `.env` hiện tại không có xung đột Encryption Key (lỗi F-002 đã được giải quyết). 
  - `frontend/.env` chỉ chứa biến môi trường an toàn (Vite Supabase Anon Key, thuộc loại Publishable Key).
  - Tệp chứa dữ liệu nhạy cảm cực cao là `keys.txt` (chứa Fireant Bearer Tokens) đã được đưa vào danh sách đen của `.gitignore`, hoàn thành yêu cầu bảo mật mã nguồn trước khi đẩy lên Git.

---

## F-015: Positional Mapping Anti-Pattern gây Garbage Data (V5)

| Field | Value |
|---|---|
| **Severity** | 🔴 CATASTROPHIC (Đã xử lý) |
| **Component** | `providers/vietcap.py` & `golden_schema.json` |
| **Impact** | Dữ liệu metric bị trượt dòng. EPS bị ghi nhầm thành Lợi Nhuận, v.v. |

**Chi tiết:**
- Các keys như `isaX`, `bsaX` là index vị trí theo tuần tự động từ API, không phải định danh ngữ nghĩa. Nếu công ty khuyết 1 dòng, toàn bộ index bị dồn lên làm sai lệch ánh xạ.
- **Hành động & Giải pháp:** Đã tiến hành **Exact Ground Truth Mapping** bằng cách kiểm tra thủ công với BCTC thật và khóa cứng 22 core metrics. Đã xóa dữ liệu sai và resync thành công cho VN30.

---

## F-016: Synchronous Pipeline Performance Bottlenecks (CTO Audit)

| Field | Value |
|---|---|
| **Severity** | 🔴 HIGH (Technical Debt) |
| **Component** | `v5_full_resync.py`, `pipeline.py`, Parquet Storage |
| **Impact** | Hao phí khổng lồ RAM, CPU, gây treo terminal và mất >45 phút sync 30 mã. |

**Chi tiết CTO Audit:**
1. **Lạm dụng Subprocess:** Batch script chạy tuần tự 31 lệnh `subprocess.run(python)`, bắt OS tạo/hủy Python Interpreter 31 lần.
2. **Schema Phình to:** `golden_schema.json` (~1MB) chứa quá nhiều `sample_values` không phục vụ runtime.
3. **I/O Disk dư thừa:** ETL ghi ra file Parquet sau đó lại đọc Parquet lên lại để sync db.

**Hành động & Giải pháp (Kế hoạch Phase 5.5):**
- Trích xuất file `lite_schema.json` siêu tinh gọn.
- Gộp Pipeline & Sync vào chạy bằng `asyncio` hoặc `ThreadPoolExecutor` trên một Python Interpreter duy nhất.
- Bỏ bước lưu Parquet ổ cứng cho tác vụ daily sync, chạy trực tiếp Pandas → Supabase db.

> **⚠️ Bản ghi cập nhật kết thúc (End of Report)**
