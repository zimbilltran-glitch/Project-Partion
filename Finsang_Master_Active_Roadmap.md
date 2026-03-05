# 🚀 Finsang Master Active Roadmap

Bảng theo dõi lộ trình phát triển tổng thể của siêu dự án Finsang.

> **Cập nhật lần cuối:** 2026-03-05 | **Phase Hiện Tại:** Phase 7.0 — Production Readiness (Finishing)

## 📌 Phase Overview

| Tên Giai Đoạn | Mã Hệ Thống | Trạng Thái | Tiến Độ / Mục Tiêu |
|---|---|---|---|
| Phase 1.0 - Core ETL Framework | `Version_1` & `Version_2` | ✅ Hoàn thành | Pipeline, Golden Schema, Fernet AES-128. |
| Phase 2.0 - React Web Dashboard | `frontend` base | ✅ Hoàn thành | UI cơ bản, BCTC tables, Supabase, Dark Mode. |
| Phase 3.0 - Simply Wall St 360 Overview | `V3_SimplyWallSt` | ✅ Hoàn thành | Radar chart, Valuation Gauge, Sector-specific summary. |
| Phase 4.0 - Analysis Charts Integration | `V4_Chart_Improve` | ✅ Hoàn thành | `recharts`, biểu đồ chuyên sâu 3 Sector. |
| Phase 5.0 - Data Integrity (Exact Ground Truth) | `V5_improdata` | ✅ Hoàn thành | Semantic mapping thay Positional. Resync sạch 100% VN30. |
| Phase 5.5 - Pipeline Performance Tuning | `V5_improdata` | ✅ Hoàn thành | `lite_schema` + ThreadPool async + Stream-to-DB. |
| Phase 5.6 - Sector Metrics Completion | `Version_2` | ✅ Hoàn thành | LDR, CIR, Margin/Equity, CER. (CASA: API Limit). |
| Phase 6.0 - PDF Financial Parsing | `PDF_TRANS_Pipeline` | ⏳ Chờ | Bóc tách PDF BCTC → Markdown/CSDL. |
| Phase 7.0 - Production Readiness | `frontend` deploy | 🚀 **ACTIVE** | `npm run build` ✅, RLS Hardened ✅, Bandit Clean ✅. |

---

## 🗺️ Roadmap Chi Tiết — Kế Hoạch Trả Nợ Kỹ Thuật

### Giai Đoạn 1 — Pipeline Performance (✅ HOÀN THÀNH)
> **Mục tiêu:** Tăng tốc re-sync để mọi bước verify sau đó nhanh, tránh tốn quota.

- [x] Tạo `lite_schema.json` (strip `sample_values`, target < 50KB)
- [x] Refactor `v5_full_resync.py` → `ThreadPoolExecutor` (bỏ `subprocess.run`)
- [x] Stream Pandas → Supabase trực tiếp, Parquet là backup tách biệt
- [x] **Kết quả:** Resync 30 mã VN30 chỉ mất ~27.5 giây (Wall time).

### Giai Đoạn 2 — Data Mapping Verification & SEC Research (✅ HOÀN THÀNH)
> **Phụ thuộc:** Giai đoạn 1 hoàn thành.

- [x] Probe Vietcap API prefix SEC (`iss`, `cfs`, `bss`) — tìm compiler/docs chính thức
- [x] Đối chiếu dòng-dòng raw API vs `golden_schema.json` cho SSI, VCI, VND
- [x] Cập nhật schema với đúng `vietcap_key` cho nhóm ngành Chứng khoán.
- [x] Audit hardcode: Gỡ bỏ toàn bộ logic `BANK_TICKERS` hardcoded, thay bằng `sector.py`.

### Giai Đoạn 3 — Bank & SEC Metrics Completion (✅ HOÀN THÀNH)
> **Phụ thuộc:** Giai đoạn 2 verified. Làm sau khi mapping ổn định.

- [x] Tính LDR = Cho vay KH / Tiền gửi KH (Từ bsb104 và bsb113 - Đã verify)
- [x] Tính CIR = Chi phí QL / Tổng thu nhập HĐ (Từ isb39 và isb38 - Đã verify)
- [x] Probe NOTE API → CASA (Demand Deposits) — **Limitation:** API 403 Forbidden.
- [x] Bổ sung SEC metrics: Margin Lending / Equity, CER, Brokerage Share.
- [x] Chạy `run_metrics_batch.py` full VN30, verify NIM/YOEA/LDR/CIR trên Frontend thành công.

### Giai Đoạn 4 — Security & Ops Cleanup (✅ HOÀN THÀNH)
> **Mục tiêu:** Đảm bảo an toàn và quy trình vận hành.

- [x] Kiểm tra RLS `pg_policies` — Đã gỡ bỏ toàn bộ quyền INSERT/UPDATE/DELETE của `anon`.
- [x] Fix `requests` timeout=10 (Bandit Medium findings) trên toàn bộ codebase.
- [x] Viết `QUARTERLY_UPDATE_GUIDE.md` — Hướng dẫn 4 bước cập nhật hàng quý.

### Giai Đoạn 5 — Production Release (🚀 ĐANG LÀM)
> **Chỉ làm khi toàn bộ data verified 100%.**

- [x] `npm run build` thành công (Thư mục `dist/` sẵn sàng).
- [ ] Deploy lên Vercel hoặc Netlify (User tự thực hiện khi sẵn sàng).
- [ ] Set env vars production (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`).
- [ ] Verify end-to-end trên production URL.
