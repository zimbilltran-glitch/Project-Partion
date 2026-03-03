# 🎯 Finsang V5 — Data Integrity Enhancement (ImproData)
# B.L.A.S.T. Implementation Plan

> **Blueprint → Layer → Assemble → Style → Test**  
> **Date**: 2026-03-03 | **Version**: 1.0  
> **Mục tiêu**: Sửa lỗi mapping dữ liệu tài chính giữa Vietcap API → Supabase, đảm bảo **100% đúng** giá trị từng đầu mục BCTC.  
> **Scope**: Toàn bộ 3 bảng tài chính (CĐKT, KQKD, LCTT) × 3 sector (Phi tài chính, Ngân hàng, Chứng khoán).

---

## 📌 Tổng quan vấn đề

### Nguyên nhân gốc rễ (Root Cause)

Vietcap API sử dụng hệ thống key **đa tiền tố (multi-prefix)** cho Balance Sheet:

| Prefix | Ý nghĩa | Phạm vi |
|--------|---------|---------|
| `bsa`  | Tài sản (Assets) | `bsa1` → `bsa96` |
| `bsb`  | Nợ phải trả + Vốn CSH (Liabilities + Equity) | `bsb97` → `bsb179` |
| `bss`  | Sector: Chứng khoán | `bss133` → `bss257` |
| `bsi`  | Sector: Bảo hiểm | `bsi139` → `bsi287` |

**Tuy nhiên**, toàn bộ ~400 field trong `golden_schema.json` có `vietcap_key: ""` (trống).

Pipeline fallback sang logic vị trí trong `providers/vietcap.py`:
```python
# LUÔN dùng prefix "bsa" — SAI cho Nợ/Vốn (cần "bsb")
key = f"bsa{sheet_row_idx}"
```

**Hậu quả**: Mọi dòng từ row 97+ (Nợ phải trả, Phải trả người bán, Thuế...) → đọc `bsa97` thay vì `bsb97` → **giá trị sai hoàn toàn**.

Tương tự cho KQKD (`isa` vs `isb`) và LCTT (`cfa` vs `cfb`).

---

## ⚡ PHASE 1: BLUEPRINT (Phân tích & Khảo sát)

> **Agent Assignment**: Data Engineer / CFO Analyst  
> **Nhiệm vụ chính**: Map chính xác từng API key.

### Bước cần làm

1. **Fetch raw API** cho 3 ticker đại diện:
   - `FPT` (Phi tài chính), `MBB` (Ngân hàng), `SSI` (Chứng khoán)
   - Lưu vào `_raw/{ticker}_{section}.json`

2. **Extract tất cả non-null keys** từ mỗi API response:
   ```python
   # Ví dụ output cho FPT Balance Sheet:
   # bsa1=45535942846453, bsa2=9315440438884, ..., bsb97=20789..., bsb98=...
   ```

3. **Cross-reference** với `golden_schema.json` → xác định chính xác key nào ứng field nào.

### Files cần tạo/sửa
- `[NEW]` `V5_improdata/rebuild_schema_keys.py`
- `[READ]` `Version_2/golden_schema.json`
- `[READ]` `Version_2/providers/vietcap.py`

---

## ⚡ PHASE 2: LAYER (Sửa Golden Schema)

> **Agent Assignment**: Data Engineer  
> **Nhiệm vụ chính**: Populate đúng `vietcap_key` cho tất cả fields.

### Bước cần làm

1. **Chạy `rebuild_schema_keys.py`** → output: `golden_schema_v5.json` (bản sửa)
2. **Verify diff**: So sánh bản cũ vs mới, kiểm tra:
   - Không field nào còn `vietcap_key: ""`
   - Các key bắt đầu đúng prefix (`bsa` cho assets, `bsb` cho liabilities...)
3. **Cập nhật `providers/vietcap.py`**:
   - **XÓA** dict `field_mapping` (10 override cũ)
   - **XÓA** logic fallback `f"bsa{sheet_row_idx}"`
   - Đảm bảo `normalize()` **luôn** dùng `get_api_value_by_key()` (explicit key)
4. **Replace** `golden_schema.json` cũ bằng bản `_v5`.

### Files cần sửa
- `[MODIFY]` `Version_2/golden_schema.json`
- `[MODIFY]` `Version_2/providers/vietcap.py`

---

## ⚡ PHASE 3: ASSEMBLE (Re-process & Re-sync)

> **Agent Assignment**: Data Pipeline  
> **Nhiệm vụ chính**: Chạy lại toàn bộ pipeline với schema mới.

### Bước cần làm

1. **Pilot test**: Chạy `pipeline.py --ticker FPT` → kiểm tra Parquet output
2. **Spot check** 10 field quan trọng:
   | # | Field | Vietcap Web | Supabase mới |
   |---|-------|-------------|--------------|
   | 1 | Tổng tài sản | ? | ? |
   | 2 | Nợ phải trả | ? | ? |
   | 3 | Vốn chủ sở hữu | ? | ? |
   | 4 | Phải trả người bán | ? | ? |
   | 5 | Thuế & khoản phải trả NN | ? | ? |
   | 6 | Doanh thu thuần | ? | ? |
   | 7 | Lợi nhuận gộp | ? | ? |
   | 8 | LNST | ? | ? |
   | 9 | Operating CF | ? | ? |
   | 10 | Free Cash Flow | ? | ? |

3. **Nếu pass** → Chạy full VN30:
   ```bash
   python sync_supabase.py
   ```

4. **Accounting identity check**:
   ```
   Tổng TS = Nợ PT + Vốn CSH  (tolerance ±0.01%)
   ```

### Files cần chạy
- `Version_2/pipeline.py`
- `Version_2/sync_supabase.py`

---

## ⚡ PHASE 4: TEST (Validation & Audit)

> **Agent Assignment**: CFO Analyst + CTO  
> **Nhiệm vụ chính**: Đảm bảo tính chính xác tuyệt đối.

### Kiểm tra tự động

- `[NEW]` `V5_improdata/validate_vs_web.py`:
  - Fetch API cho VN30
  - So sánh từng field giữa Supabase và API
  - Output: `validation_report.json` (pass/fail per field)

### CFO Audit Rules (từ `professional-cfo-analyst` skill)
- [ ] `Tổng Tài Sản = Nợ Phải Trả + Vốn CSH` (±0.01%)
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

1. **Agent Setup**: Đọc file này + `v5_findings.md` → nắm bối cảnh. *(Bất kỳ Agent)*
2. **Schema Fix**: Chạy `rebuild_schema_keys.py` → cập nhật `golden_schema.json`. *(Data Eng)*
3. **Provider Fix**: Sửa `providers/vietcap.py` → xóa fallback logic. *(Data Eng)*
4. **Pipeline Run**: Chạy `pipeline.py` + `sync_supabase.py` cho VN30. *(Pipeline)*
5. **Validation**: Chạy `validate_vs_web.py` → xác nhận pass. *(CFO/CTO)*
6. **Release**: Cập nhật `v5_changelog.md` → commit + push. *(Any Agent)*

---

## 📎 Tham chiếu nhanh

| File | Đường dẫn | Vai trò |
|------|-----------|---------|
| Golden Schema | `Version_2/golden_schema.json` | Registry ánh xạ field → Vietcap key |
| Vietcap Provider | `Version_2/providers/vietcap.py` | Logic đọc API value (BUG ở đây) |
| Pipeline | `Version_2/pipeline.py` | Orchestrate fetch → normalize → parquet |
| Sync | `Version_2/sync_supabase.py` | Parquet → Supabase upsert |
| CFO Skill | `.agent/skills/professional-cfo-analyst/` | Audit rules & checksum |
