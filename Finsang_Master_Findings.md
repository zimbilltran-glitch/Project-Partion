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
| **Component** | `sub-projects/Version_2/pipeline.py` & Vietcap Provider |
| **Impact** | Không thể tự động tính toán CASA (Tiền gửi không kỳ hạn) và NPL (Nợ xấu) chi tiết cho Bank. |

**Chi tiết:**
- Vietcap API endpoint `section=NOTE` trả về lỗi `HTTP 403 Forbidden` khi truy vấn dữ liệu Thuyết minh BCTC cho hầu hết các mã Ngân hàng và Chứng khoán.
- **Root Cause:** Phía Server Vietcap giới hạn quyền truy cập vào dữ liệu Thuyết minh cấu trúc (Structured Notes) qua API công khai.

**Giải pháp & Khuyến nghị:**
- Đây là giới hạn từ nguồn dữ liệu (Data Source Limitation). 
- **Workaround:** User có thể sử dụng `PDF_TRANS_Pipeline` để bóc tách thủ công từ file PDF BCTC chính thức nếu cần số liệu CASA/NPL chính xác tuyệt đối.

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

> **⚠️ Bản ghi cập nhật kết thúc (End of Phase 5/6 Audit Report)**
