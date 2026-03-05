# 🚀 Finsang Master Active Roadmap

Bảng theo dõi lộ trình phát triển tổng thể của siêu dự án Finsang.

> **Cập nhật lần cuối:** 2026-03-05 | **Phase Hiện Tại:** Phase 5.5 — Pipeline Performance Tuning

## 📌 Phase Overview

| Tên Giai Đoạn | Mã Hệ Thống | Trạng Thái | Tiến Độ / Mục Tiêu |
|---|---|---|---|
| Phase 1.0 - Core ETL Framework | `Version_1` & `Version_2` | ✅ Hoàn thành | Pipeline, Golden Schema, Fernet AES-128. |
| Phase 2.0 - React Web Dashboard | `frontend` base | ✅ Hoàn thành | UI cơ bản, BCTC tables, Supabase, Dark Mode. |
| Phase 3.0 - Simply Wall St 360 Overview | `V3_SimplyWallSt` | ✅ Hoàn thành | Radar chart, Valuation Gauge, Sector-specific summary. |
| Phase 4.0 - Analysis Charts Integration | `V4_Chart_Improve` | ✅ Hoàn thành | `recharts`, biểu đồ chuyên sâu 3 Sector. |
| Phase 5.0 - Data Integrity (Exact Ground Truth) | `V5_improdata` | ✅ Hoàn thành | Semantic mapping thay Positional. Resync sạch 100% VN30. |
| **Phase 5.5 - Pipeline Performance Tuning** | `V5_improdata` | 🚀 **ACTIVE** | `lite_schema` + ThreadPool async + Stream-to-DB. |
| Phase 5.6 - Sector Metrics Completion | `Version_2` | ⏳ Sau P5.5 | Bank (LDR, CIR, CASA) + SEC metrics. Phụ thuộc NOTE API. |
| Phase 6.0 - PDF Financial Parsing | `PDF_TRANS_Pipeline` | ⏳ Chờ | Bóc tách PDF BCTC → Markdown/CSDL. |
| Phase 7.0 - Production Release | `frontend` deploy | ⏳ Chờ data ổn định | Deploy Vercel/Netlify. Chỉ làm khi data 100% verified. |

---

## 🗺️ Roadmap Chi Tiết — Kế Hoạch Trả Nợ Kỹ Thuật

### Giai Đoạn 1 — Pipeline Performance (🚀 ĐANG LÀM)
> **Mục tiêu:** Tăng tốc re-sync để mọi bước verify sau đó nhanh, tránh tốn quota.

- [ ] Tạo `lite_schema.json` (strip `sample_values`, target < 50KB)
- [ ] Refactor `v5_full_resync.py` → `ThreadPoolExecutor` (bỏ `subprocess.run`)
- [ ] Stream Pandas → Supabase trực tiếp, Parquet là backup tách biệt
- [ ] Verify: Resync 30 mã < 5 phút

### Giai Đoạn 2 — Data Mapping Verification & SEC Research
> **Phụ thuộc:** Giai đoạn 1 hoàn thành.

- [ ] Probe Vietcap API prefix SEC (`iss`, `cfs`, `bss`) — tìm compiler/docs chính thức
- [ ] Đối chiếu dòng-dòng raw API vs `golden_schema.json` cho SSI, VCI, VND
- [ ] Cập nhật schema nếu phát hiện sai mapping
- [ ] Audit hardcode: `grep -r "BANK_TICKERS"` toàn codebase → đảm bảo 100% dùng `sector.py`

### Giai Đoạn 3 — Bank & SEC Metrics Completion
> **Phụ thuộc:** Giai đoạn 2 verified. Làm sau khi mapping ổn định.

- [ ] Tính LDR = Cho vay KH / Tiền gửi KH (từ CDKT_BANK — sẵn sàng)
- [ ] Tính CIR = Chi phí HĐ / Thu nhập HĐ thuần (từ KQKD_BANK — sẵn sàng)
- [ ] Probe NOTE API → tìm key CASA (Demand Deposits) cho Bank
- [ ] Bổ sung SEC metrics vào `calc_sec_metrics()` (từ kết quả GĐ 2)
- [ ] Chạy `run_metrics_batch.py` full VN30, verify NIM/YOEA/LDR/CIR trên Frontend

### Giai Đoạn 4 — Security & Ops Cleanup
> **Làm sau khi data ổn định.**

- [ ] Kiểm tra lại RLS `pg_policies` — `anon` chỉ SELECT
- [ ] Fix `requests` timeout=10 (Bandit Medium findings) trên `tools/`
- [ ] Viết `QUARTERLY_UPDATE_GUIDE.md`

### Giai Đoạn 5 — Production Release (⏳ Ưu tiên thấp)
> **Chỉ làm khi toàn bộ data verified 100%.**

- [ ] `npm run build` + Deploy Vercel/Netlify
- [ ] Set env vars production
- [ ] Verify end-to-end trên production URL
