# 🎯 Finsang V5 — Data Integrity Enhancement (ImproData)
# B.L.A.S.T. Implementation Plan

> **Blueprint → Layer → Assemble → Style → Test**  
> **Date**: 2026-03-03 → 2026-03-04 | **Version**: 2.0 (Updated after Phase 3)  
> **Mục tiêu**: Sửa lỗi mapping dữ liệu tài chính giữa Vietcap API → Supabase, đảm bảo **100% đúng** giá trị từng đầu mục BCTC.  
> **Scope**: Toàn bộ 3 bảng tài chính (CĐKT, KQKD, LCTT) × 3 sector (Phi tài chính, Ngân hàng, Chứng khoán).

---

## 📌 Tổng quan vấn đề

### Nguyên nhân gốc rễ (Root Cause)

Vietcap API sử dụng hệ thống key cho Balance Sheet **khác với giả định ban đầu**:

| Prefix | Thực tế | Mô tả |
|--------|---------|-------|
| `bsa`  | **ALL items** cho Normal company | bsa1-52 (Assets), bsa53 (Total), bsa54-77 (Liab), bsa78-95 (Equity), bsa96 (Total Source), bsa159+ (Phụ) |
| `bsb`  | Bank-specific items | bsb97-263 |
| `bss`  | Securities sector | bss133-257 |
| `bsi`  | Insurance sector | bsi139-287 |

> ⚠️ **BÀI HỌC**: `bsa` KHÔNG phải chỉ "Assets". Nó chứa TOÀN BỘ BCTC cho normal company.

**Pipeline fallback cũ** (`f"bsa{sheet_row_idx}"`) tạo sequential mapping sai vì schema order ≠ API key order.

---

## ✅ PHASE 1: BLUEPRINT (Phân tích & Khảo sát) — HOÀN TẤT

> **Thời gian**: 2026-03-03 | **Scripts**: `phase1_analyze.py`

### Kết quả
- Fetch raw API cho FPT (normal), MBB (bank), SSI (sec) → lưu `_raw/`
- **345 fields trống** `vietcap_key` (CDKT: 122, KQKD: 25, LCTT: 41, NOTE: 157)
- **601 fields đã map** (Bank + SEC sectors = 100% coverage)
- FPT BS có 123 bsa keys: block chính 1-96 (96 keys liên tục) + block phụ 159-278 (27 keys)
- Report: `v5_phase1_report.json`

---

## ✅ PHASE 2: LAYER (Sửa Golden Schema) — HOÀN TẤT

> **Thời gian**: 2026-03-04 | **Scripts**: `rebuild_schema_keys.py`

### Chiến lược đã dùng: SEGMENTED MAPPING

**Vấn đề với Sequential mapping**: Schema có 65 fields Assets, API chỉ có 52 keys Assets → lệch từ field[52] trở đi.

**Giải pháp**: Chia CDKT thành segments dựa trên cấu trúc BCTC:

```
Schema fields [0..64]   → bsa1..bsa52   (Assets, 13 fields không có key)
Schema field  [65]      → bsa53         (TỔNG TÀI SẢN — anchor từ Bank schema)
Schema fields [66..96]  → bsa54..bsa77  (NỢ PHẢI TRẢ, 7 fields không có key)
Schema fields [97..120] → bsa78..bsa95 + bsa159+  (VỐN CSH + supplementary)
Schema field  [121]     → bsa96         (TỔNG NGUỒN VỐN)
```

**Bank Schema Ground Truth**: Fields CDKT_BANK dùng `bsa` prefix cho shared items → cùng key number cho normal company. Ví dụ: Bank field "TỔNG TÀI SẢN" = `bsa53` → confirm `bsa53` cho normal company.

### Kết quả
- **188 fields** đã được populate `vietcap_key` (CDKT: 122, KQKD: 25, LCTT: 41)
- **73 CDKT key corrections** so với sequential mapping
- **9 name-based corrections** từ Bank schema
- Xóa `field_mapping` dict (10 overrides) + fallback `f"bsa{idx}"` trong `vietcap.py`

### Files đã sửa
- `Version_2/golden_schema.json` — rebuilt
- `Version_2/providers/vietcap.py` — cleaned

---

## 🔄 PHASE 3: ASSEMBLE (Re-sync & Verify) — ĐANG THỰC HIỆN

> **Thời gian**: 2026-03-04 | **Scripts**: `validate_spotcheck.py`

### P3.1 ✅ Pipeline pilot (FPT)
```
CDKT: 4880 rows | Mapped: 85.2% (109/122 fields có key)
KQKD: 1000 rows | Mapped: 100%
LCTT: 1640 rows | Mapped: 100%
NOTE: 6280 rows | Mapped: 0% (expected — API không hỗ trợ)
```

### P3.2 ✅ Spot check (12 fields)

| # | Field | Mapped Key | Parquet Value | API Value | Match |
|---|-------|-----------|---------------|-----------|-------|
| 1 | Tổng cộng tài sản | bsa53 | 71,999,995,678,620 | 71999995678620.0 | ✅ |
| 2 | TÀI SẢN NGẮN HẠN | bsa1 | 45,535,942,846,453 | 45535942846453.0 | ✅ |
| 3 | TÀI SẢN DÀI HẠN | bsa27 | 381,508,926,294 | 381508926294.0 | ✅ |
| 4 | NỢ PHẢI TRẢ | bsa54 | 36,272,455,573,820 | 36272455573820.0 | ✅ |
| 5 | VỐN CHỦ SỞ HỮU | bsa78 | 35,727,540,104,800 | 35727540104800.0 | ✅ |
| 6 | Phải trả người bán | bsa56 | 14,446,238,451,323 | 14446238451323.0 | ✅ |
| 7 | Thuế & KP trả NN | bsa58 | 562,066,755,666 | 562066755666.0 | ✅ |
| 8 | Tổng cộng nguồn vốn | bsa96 | 71,999,995,678,620 | 71999995678620.0 | ✅ |
| 9 | Doanh thu thuần | isa3 | 62,848,794,351,367 | 62848794351367.0 | ✅ |
| 10 | Lợi nhuận gộp | isa5 | 23,698,348,369,916 | 23698348369916.0 | ✅ |
| 11 | Lãi thuần sau thuế | isa21 | 1,570,654,718,266 | 1570654718266.0 | ✅ |
| 12 | LN cổ đông công ty mẹ | isa23 | 4,944 | 4944.0 | ✅ |

### P3.2 ✅ Accounting Identity
```
✅ Assets == Nguồn Vốn? PASS (Diff: 0)
✅ Assets == Liab + Equity? PASS (Diff: 0)
```

### P3.3 ⬜ Sync VN30 → Supabase (PENDING)
- Chạy `sync_supabase.py` cho toàn bộ VN30
- Cần `SUPABASE_URL` + `SUPABASE_KEY` environment variables

### P3.4 ⬜ Accounting identity cho VN30 (PENDING)

---

## ⚡ PHASE 4: TEST (Validation & Audit) — CHƯA BẮT ĐẦU

> **Agent Assignment**: CFO Analyst + CTO

### Kiểm tra tự động
- `[EXISTS]` `V5_improdata/validate_spotcheck.py` — spot check + accounting identity
- `[NEW]` `V5_improdata/validate_vs_web.py` — so sánh Supabase vs API cho VN30

### CFO Audit Rules (từ `professional-cfo-analyst` skill)
- [x] `Tổng Tài Sản = Nợ Phải Trả + Vốn CSH` (±0.01%) — ✅ PASS cho FPT
- [ ] `Net CF = Operating CF + Investing CF + Financing CF`
- [ ] Không có giá trị NULL cho core fields
- [ ] Dự phòng (provision) luôn âm hoặc zero
- [ ] Khấu hao lũy kế luôn âm

### CTO Audit
- [ ] Pipeline idempotent (chạy lại = không duplicate)
- [ ] Không secrets hardcoded
- [ ] Log pipeline_runs đầy đủ

---

## 🗺️ Execution Roadmap (Trình tự chạy Agent)

1. ✅ **Agent Setup**: Đọc file này + `v5_findings.md` → nắm bối cảnh.
2. ✅ **Schema Fix**: Chạy `rebuild_schema_keys.py` → cập nhật `golden_schema.json`.
3. ✅ **Provider Fix**: Sửa `providers/vietcap.py` → xóa fallback logic.
4. ⬜ **Pipeline Run**: Chạy `pipeline.py` + `sync_supabase.py` cho VN30.
5. ⬜ **Validation**: Chạy `validate_vs_web.py` → xác nhận pass.
6. ⬜ **Release**: Cập nhật `v5_changelog.md` → commit + push.

---

## 📎 Tham chiếu nhanh

| File | Đường dẫn | Vai trò |
|------|-----------|---------|
| Golden Schema | `Version_2/golden_schema.json` | Registry ánh xạ field → Vietcap key (**ĐÃ SỬA**) |
| Vietcap Provider | `Version_2/providers/vietcap.py` | Logic đọc API value (**ĐÃ SỬA** — xóa fallback) |
| Pipeline | `Version_2/pipeline.py` | Orchestrate fetch → normalize → parquet |
| Sync | `Version_2/sync_supabase.py` | Parquet → Supabase upsert |
| Spot Check | `V5_improdata/validate_spotcheck.py` | 12-field validation + accounting identity |
| Rebuild Script | `V5_improdata/rebuild_schema_keys.py` | Segmented mapping builder |
| Phase 1 Report | `V5_improdata/v5_phase1_report.json` | Raw audit results |
| CFO Skill | `.agent/skills/professional-cfo-analyst/` | Audit rules & checksum |
