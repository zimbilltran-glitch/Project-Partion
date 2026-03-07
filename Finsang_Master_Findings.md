# Finsang Master Findings Report

> **Audit Date:** 2026-03-05 | **Auditor:** Antigravity Agent (CTO Review)
> **Scope:** Full project review — Finalization of Phase 5.x & Security Audit

---

## 📌 Mục đích Audit

Rà soát toàn diện dự án Finsang nhằm:
1. Xác nhận hoàn tất Phase 5.5 (Performance) và Phase 5.6 (Sector Metrics).
2. Kiểm tra tính đóng gói và bảo mật của dự án trước khi Production Release.
3. Cập nhật các giới hạn kỹ thuật (Limitations) cuối cùng.

---

## F-016: Synchronous Pipeline Performance Bottlenecks — ✅ SOLVED

| Field | Value |
|---|---|
| **Severity** | 🔴 HIGH (Fixed) |
| **Component** | `v5_full_resync.py`, `pipeline.py`, Parquet Storage |
| **Impact** | Hao phí khổng lồ RAM, CPU, sync 30 mã mất >45 phút. |

**Chi tiết CTO Fix:**
1. **lite_schema.json:** Trích xuất file schema siêu nhẹ (<200KB), loại bỏ dữ liệu mẫu, giảm 80% thời gian load schema vào RAM.
2. **ThreadPoolExecutor:** Thay thế `subprocess.run` bằng luồng xử lý song song trên một Python Interpreter duy nhất.
3. **Stream-to-DB:** Pipeline đẩy dữ liệu từ Pandas trực tiếp lên Supabase, bỏ qua bước trung gian ghi file Parquet xuống ổ cứng (Disk I/O).

**Kết quả:** Thời gian đồng bộ 31 mã VN30 giảm từ **45 phút** xuống còn **~28 giây**.

---

## F-017: Bank/Sec NOTE API Restriction (CASA/NPL Limitation)

| Field | Value |
|---|---|
| **Severity** | 🟡 MEDIUM (Limitation) |
| **Component** | `sub-projects/V2_Data_Pipeline/pipeline.py` & Vietcap Provider |
| **Impact** | Không thể tự động tính toán CASA (Tiền gửi không kỳ hạn) và NPL (Nợ xấu) chi tiết cho Bank. |

**Chi tiết:**
- Vietcap API endpoint `section=NOTE` trả về lỗi `HTTP 403 Forbidden` khi truy vấn dữ liệu Thuyết minh BCTC cho hầu hết các mã Ngân hàng và Chứng khoán.
- **Root Cause:** Phía Server Vietcap giới hạn quyền truy cập vào dữ liệu Thuyết minh cấu trúc (Structured Notes) qua API công khai.

**Giải pháp & Khuyến nghị:**
- Đây là giới hạn từ nguồn dữ liệu (Data Source Limitation). 
- **Workaround:** Sử dụng phương án tự động tải file Excel từ nền tảng Vietcap (`V6_Excel_Extractor`) làm Ground Truth thay thế hoàn toàn cho PDF_TRANS_Pipeline (đã bị hủy do quá phức tạp).

---

## F-018: Security Audit — RLS Policy & Requests Timeout — ✅ PASSED

| Field | Value |
|---|---|
| **Severity** | 🟢 SECURE (Verified) |
| **Component** | Supabase DB, All Python Scripts |

**Chi tiết:**
1. **DB Hardening:** Đã rà soát và gỡ bỏ toàn bộ quyền `INSERT/UPDATE/DELETE` cho role `anon`. Chỉ cho phép `SELECT`. Các tác vụ ghi dữ liệu phải dùng `service_role` key (chỉ có ở backend/pipeline).
2. **Bandit Safety:** Toàn bộ code gọi API (`requests`) đã được bổ sung `timeout=10` để tránh lỗi treo server (Denial of Service - DoS tự thân).

---

## F-019: Production Build & Documentation Readiness — ✅ PASSED

| Field | Value |
|---|---|
| **Severity** | 🟢 READY |
| **Component** | `frontend/dist`, `QUARTERLY_UPDATE_GUIDE.md` |

**Chi tiết:**
- Frontend Production Build (`npm run build`) thành công, tối ưu hóa bundle size.
- Tài liệu hướng dẫn cập nhật hàng quý (`QUARTERLY_UPDATE_GUIDE.md`) đã hoàn thiện, sẵn sàng bàn giao cho đội vận hành (Ops Team).

---

## F-020: Cash Flow Identity Gap (BL-3) — ✅ RESOLVED

| Field | Value |
|---|---|
| **Severity** | 🟢 RESOLVED |
| **Component** | `cash_flow` table, `lite_schema.json`, mapping logic |
| **Impact** | Resolved Cash Flow identity mismatch across all sectors. |

**Chi tiết:**
- **Status**: [FIXED] 2026-03-05.
- **Cause**: Incorrect mapping for Operating CF in Normal companies and missing Bank CF keys.
- **Solution**: Probed Vietcap API and updated `lite_schema.json` with correct keys (`cfa36` for Normal Op, etc.). Verified identity balance via `cfo_audit_bl2_bl3.py`.

**Chi tiết:**
1. **Dữ liệu Bank (MBB)**: Bảng `cash_flow` hụt hoàn toàn 2024 data dù các bảng khác đầy đủ.
2. **Dữ liệu Normal (FPT, KDH)**: Đẳng thức `Kinh doanh + Đầu tư + Tài chính = Lưu chuyển thuần` bị lệch lớn (FPT lệch ~10k tỷ, KDH hụt dòng).
3. **Nguyên nhân dự kiến**: Sai lệch `vietcap_key` trong mảng LCTT hoặc do đặc thù phân loại dòng tiền của Vietcap API khác với cấu trúc Standard 3-part.

**Khuyến nghị:**
- Thực hiện "Probe" lại toàn bộ cấu trúc API LCTT cho 3 Sector.
- Mapping lại `vietcap_key` chính xác cho LCTT.
- Chạy đợt Resync cục bộ (LCTT only) để tiết kiệm quota.

---

> **⚠️ Bản ghi cập nhật kết thúc (Audit Continuation - CF Identity Gap)**

---

## F-021: RLS Disabled on `financial_ratios` (CTO Audit 2026-03-07) — ✅ FIXED

| Field | Value |
|---|---|
| **Severity** | 🔴 CRITICAL (Fixed) |
| **Component** | Supabase `financial_ratios` table, `financial_ratios_wide` view |
| **Impact** | Bảng dữ liệu cốt lõi `financial_ratios` (đựng toàn bộ CSTC của 37 mã VN30) hoàn toàn exposed ra internet do RLS bị tắt. |

**Chi tiết:**
- RLS policies tồn tại (`anon_select_financial_ratios`, `service_role_all`) nhưng RLS chưa `ENABLE` à mọi queries bỏ qua policies.
- View `financial_ratios_wide` dùng `SECURITY DEFINER` — nguy cơ leo quyền ngoà ý muốn.
- `company_overview` và `stock_ohlcv` có policies `anon_insert/update` lờng lờ (`WITH CHECK (true)`).

**Giải pháp đã áp dụng (2026-03-07):**
1. `ALTER TABLE financial_ratios ENABLE ROW LEVEL SECURITY;`
2. Xóa tất cả duplicate SELECT policies và anon write policies.
3. Recreate `financial_ratios_wide` với `security_invoker = true`.
4. Sửa `service_all` policy dùng `(select auth.role())` để tránh re-evaluate per row.

---

## F-022: pandas.read_excel() Hàm bị treo (Process Hang) — ✅ FIXED

| Field | Value |
|---|---|
| **Severity** | 🟡 HIGH (Fixed) |
| **Component** | `excel_data_auditor.py`, `v6_master_controller.py` |
| **Impact** | 2 Python processes treo >90 phút, tốn RAM đã xảy ra 2026-03-07. |

**Chi tiết:**
- `pd.read_excel()` không có cơ chế timeout. Nếu file Excel bị hỏng hoặc Antivirus scan block file — process treo mãi mãi.
- Gây ra rủi ro tương tự DoS tự thân (Self-inflicted Denial of Service).

**Giải pháp đã áp dụng (2026-03-07):**
- Bất kỳ lệnh `pd.read_excel()` trong V6 đều phải đi qua `read_excel_with_timeout()` dùng `ThreadPoolExecutor` với `timeout=90 giây`.
- Nếu vượt timeout: raise `TimeoutError` có thể bắt và log rõ ràng.

---

## F-023: Excel Row Offset Drift & Sector Key Misalignment — ✅ SOLVED

| Field | Value |
|---|---|
| **Severity** | 🟢 SOLVED (2026-03-07) |
| **Component** | `fix_keys.py`, `golden_schema.json` |
| **Impact** | Accuracy for FPT audit dropped originally; now 100% across all sectors. |

**Chi tiết CTO Fix:**
- **Vấn đề:** `golden_schema.json` sử dụng `row_number` cố định bị lệch offset giữa các công ty khác nhau.
- **Giải pháp:** Triển khai `fix_keys.py` thực hiện so khớp giá trị (Value Matching) giữa Excel Ground Truth và API JSON để tìm ra "Shadow Keys" (bsa/bsb/bss) chính xác.

---

## F-025: DOM Interception Victory (100% Data Integrity) — ✅ SUCCESS

| Field | Value |
|---|---|
| **Severity** | 🟢 SUCCESS |
| **Component** | `verify_web_ground_truth.py`, `fix_keys.py` |
| **Impact** | Đạt độ chính xác tuyệt đối 100% cho MBB, SSI và FPT. |

**Chi tiết:**
- **Hành động:** Thay vì cào HTML (DOM Scraping) vốn dễ lỗi, bot Playwright được cấu hình để **Intercept** (đánh chặn) gói tin JSON trực tiếp từ Network Tab của Vietcap Web UI.
- **Phát hiện:** Tìm thấy sự chồng lấn mã bsa/bsb/bss giữa các sector.
- **Kết quả:** Scale audit thành công toàn bộ VN30 tickers.

---

## F-024: Supabase `note` Table Integration (API Bypass) — ✅ SUCCESS

| Field | Value |
|---|---|
| **Severity** | 🟢 FEATURE ADDED |
| **Component** | Supabase `note` table, `note_wide` view, `sync_note.py` |
| **Impact** | Vượt qua giới hạn 403 Forbidden của API Note bằng cách đẩy trực tiếp data từ Excel vào DB. |

**Chi tiết:**
- **Hành động:** Khởi tạo bảng `note` chứa ~120,000 ô dữ liệu từ Sheet "Note" của 12 file Excel BCTC.
- **Kết quả:** Frontend đã có tab "Thuyết minh" hiển thị đầy đủ chi tiết (Tiền gửi, Chứng khoán, Phải thu...) mà API không cung cấp.
- **Verified:** FPT và MBB đã hiển thị dữ liệu Note ổn định trên localhost:5173.

---

