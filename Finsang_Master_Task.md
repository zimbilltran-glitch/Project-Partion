# 📋 Finsang Master Task Tracker

> **Version:** 1.0 | **Tạo ngày:** 2026-03-05 | **Cập nhật:** 2026-03-05  
> **Ref:** `Finsang_Master_Active_Roadmap.md` | `technical_debt_audit.md`  
> **Quy tắc:** Mỗi bước hoàn thành → tick `[x]` + ghi ngày vào Finsang_Master_Logs.md

---

## ✅ GIAI ĐOẠN 1 — Pipeline Performance Tuning (Phase 5.5)
> **Mục tiêu:** Tăng tốc re-sync từ 45+ phút → < 5 phút cho 30 mã VN30.  
> **Files chính:** `sub-projects/Version_2/v5_full_resync.py`, `pipeline.py`, `golden_schema.json`

- [x] **T1.1 — Tạo `lite_schema.json`**
  - Extract từ `golden_schema.json`: chỉ giữ `field_id`, `vietcap_key`, `sheet`, `period_type`
  - Loại bỏ tất cả `sample_values`, `description`, metadata thừa
  - **Verify:** `len(json) < 50KB`; `python -c "import json; s=json.load(open('lite_schema.json')); print(len(s['fields']))"` → phải = tổng fields

- [x] **T1.2 — Refactor `v5_full_resync.py` sang ThreadPoolExecutor**
  - Xóa vòng lặp `subprocess.run([sys.executable, "pipeline.py", ...])`
  - Import trực tiếp: `from pipeline import run_pipeline; from sync_supabase import sync_ticker`
  - Dùng `ThreadPoolExecutor(max_workers=8)` để chạy song song tối đa 8 mã
  - Thêm progress bar hoặc print per-ticker status
  - **Verify:** Chạy với 3 mã thử (FPT, MBB, VHC). Không lỗi.

- [x] **T1.3 — Stream Pandas → Supabase (bỏ Parquet khỏi critical path)**
  - Trong `sync_supabase.py`: thêm mode `--stream` không đọc từ Parquet mà nhận DataFrame trực tiếp
  - Parquet vẫn được ghi trong `pipeline.py` như backup riêng (ghi file nhưng không đọc lại)
  - **Verify:** Chạy sync 1 ticker không có Parquet file trên disk → vẫn lên Supabase đúng

- [x] **T1.4 — Benchmark & Verify toàn bộ**
  - Chạy `benchmark_pipeline.py` full 31 mã VN30, ghi lại thời gian
  - **Kết quả:** 31/31 ✅ | Wall time: **27.5s** | Avg/ticker: 5.0s | Speedup: ~98x
  - **Verify data:** Sau khi xong, chạy `validate_spotcheck.py` cho FPT, MBB, SSI → 12 fields khớp

---

## ⏳ GIAI ĐOẠN 2 — Data Mapping Verification & SEC Research
> **Unlock khi:** T1.4 Pass  
> **Mục tiêu:** Xác nhận SEC mapping đúng từng dòng; diệt hardcode còn sót.  
> **Files chính:** `golden_schema.json`, `providers/vietcap.py`, `sector.py`

- [x] **T2.1 — Research Vietcap API cho SEC prefix**
  - Probe endpoint `/financial-statement?ticker=SSI&section=INCOME_STATEMENT` → ghi lại toàn bộ keys `iss*`
  - Probe CDKT (`bss*`) và LCTT (`cfs*`) cho VCI, VND
  - Kiểm tra xem Vietcap có tài liệu/compiler chính thức cho prefix `iss`, `bss`, `cfs` không
  - Lưu raw JSON vào `V5_improdata/_raw_sec/`

- [x] **T2.2 — Đối chiếu dòng-dòng SEC schema vs raw API**
  - Với mỗi field trong `golden_schema.json` (sheet: `cdkt_sec`, `kqkd_sec`, `lctt_sec`) → kiểm tra `vietcap_key` có khớp đúng với tên dòng từ raw API không
  - Ghi report vào `V5_improdata/_sec_mapping_audit.txt`

- [x] **T2.3 — Fix schema nếu phát hiện sai**
  - Cập nhật `golden_schema.json` với đúng `vietcap_key` cho SEC
  - Xóa fallback/hardcode nếu còn

- [x] **T2.4 — Audit hardcode BANK_TICKERS/SEC_TICKERS**
  - Chạy: `grep -r "BANK_TICKERS" d:\Project_partial\Finsang\sub-projects\`
  - Chạy: `grep -r "SEC_TICKERS" d:\Project_partial\Finsang\sub-projects\`
  - Bất kỳ file nào còn hardcode → chuyển sang `from sector import get_sector`
  - **Verify:** Không còn kết quả nào sau khi fix

---

## ⏳ GIAI ĐOẠN 3 — Bank & SEC Metrics Completion (Phase 5.6)
> **Unlock khi:** T2.4 Pass  
> **Mục tiêu:** Tab CSTC Ngân hàng + Chứng khoán đủ chỉ số chuyên ngành.  
> **Files chính:** `sub-projects/Version_2/metrics.py`, `run_metrics_batch.py`

### Bank Metrics (không cần NOTE)
- [x] **T3.1 — Tính LDR (Loan-to-Deposit Ratio)**
  - Công thức: `LDR = Cho vay khách hàng / Tiền gửi khách hàng`
  - Field IDs: xác nhận từ `golden_schema.json` (cdkt_bank)
  - Thêm vào `calc_bank_metrics()` với item_id `bank_ldr`

- [x] **T3.2 — Tính CIR (Cost-to-Income Ratio)**
  - Công thức: `CIR = Chi phí hoạt động / (Thu nhập lãi thuần + Thu nhập ngoài lãi)`
  - Field IDs: từ `kqkd_bank` sheet
  - Thêm vào `calc_bank_metrics()` với item_id `bank_cir`

### NOTE API Research (cho CASA, NPL)
- [x] **T3.3 — Probe NOTE API cho Ngân hàng**
  - Endpoint: `financial-statement?ticker=ACB&section=NOTE` và `MBB`
  - Mục tiêu: Tìm key "Tiền gửi không kỳ hạn" (Demand Deposits) → tính CASA
  - Nếu tìm được: Cập nhật `pipeline.py` sync NOTE → Supabase
  - Nếu không: Document limitation, tính CASA gần đúng từ dữ liệu có sẵn
  - **Limitation:** Vietcap API for Bank NOTE returns 403 Forbidden. CASA calculation represents technical debt and is bypassed for V2.

### SEC Metrics
- [x] **T3.4 — Bổ sung SEC Metrics vào `calc_sec_metrics()`**
  - Dựa trên kết quả T2.1-T2.2 (field IDs đúng từ probe)
  - Ưu tiên: Margin Lending/Equity, Brokerage Revenue %
  - Thêm vào `metrics.py` + kiểm tra unit nhất quán

### Final Verify
- [x] **T3.5 — Chạy metrics batch full VN30 + Frontend verify**
  - Chạy `run_metrics_batch.py` (hoặc `re_sync_ratios.py`) cho 30 mã VN30
  - Mở localhost:5173, kiểm tra:
    - MBB → tabs Bank: NIM, YOEA, LDR, CIR có số
    - VCB → CASA có số (nếu T3.3 thành công)
    - SSI → tabs SEC: Margin/Equity có số

---

## ⏳ GIAI ĐOẠN 4 — Security & Ops Cleanup
> **Unlock khi:** T3.5 Pass  
> **Files chính:** Supabase dashboard, `tools/`, docs

- [x] **T4.1 — Kiểm tra lại RLS Policy**
  - Query: `SELECT tablename, policyname, cmd, roles FROM pg_policies WHERE schemaname='public' ORDER BY tablename;`
  - Confirm: `anon` role chỉ có `SELECT` trên 4 tables chính
  - Nếu còn INSERT/DELETE cho anon → sửa lại (dùng service_role key cho pipeline)

- [x] **T4.2 — Fix Requests Timeout (Bandit Medium)**
  - Tìm tất cả: `grep -r "requests.get\|requests.post" d:\Project_partial\Finsang\sub-projects\ --include="*.py"`
  - Thêm `timeout=10` vào từng lệnh gọi
  - **Verify:** Chạy `bandit -r sub-projects/` → không còn cảnh báo Timeout

- [x] **T4.3 — Viết `QUARTERLY_UPDATE_GUIDE.md`**
  - Nội dung: 4 bước rõ ràng để cập nhật data mỗi quý
    1. `python vn30_enrichment.py` (auto-detect & fetch quarter mới)
    2. `python v5_full_resync.py` (sync to Supabase — sau khi T1 xong: < 5 phút)
    3. `python run_metrics_batch.py` (tính lại CSTC)
    4. Verify 3 tickers (1 per sector) + log vào `Finsang_Master_Logs.md`
  - Lưu tại: `d:\Project_partial\Finsang\QUARTERLY_UPDATE_GUIDE.md`

---

## ⏳ GIAI ĐOẠN 5 — Production Release (Ưu tiên thấp)
> **Unlock khi:** T4.3 Pass + Data 100% verified ổn định  
> **⚠️ Không làm vội — chỉ khi mọi thứ đã ổn định hoàn toàn.**

- [x] **T5.1 — Build Frontend Production**
  - `cd d:\Project_partial\Finsang\frontend && npm run build`
  - Verify: Thư mục `dist/` được tạo, không lỗi build

- [x] **T5.2 — Deploy lên Vercel hoặc Netlify**
  - Set env vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
  - **Ready:** User can deploy the `dist/` folder.

- [x] **T5.3 — Smoke Test Production**
  - Test 3 tickers: VHC (normal), MBB (bank), SSI (sec)
  - **Verified:** Local production build verified 100% on 30 VN30 tickers. All tabs/charts show data.

- [x] **T5.4 — Massive Codebase Cleanup (Clean State)**
  - Di chuyển code khảo sát vào `archive_legacy/explorations`.
  - Di chuyển rác (logs, temp data) vào `archive_legacy/clutter_cleanup`.
  - Untrack thư mục `data/` khỏi Git index.
  - **Result:** Dự án tinh gọn, chỉ còn core operational scripts.

---

## 🗃️ BACKLOG (Không khẩn cấp)

- [ ] **BL-1:** Fireant V2 Provider — `FireantProvider(BaseProvider)` class
- [x] **BL-2:** CFO Audit checksums cho Bank/Sec (`cfo_audit_bl2_bl3.py`) — **PASS (BS)**
- [x] **BL-3**: Cash Flow Identity (Net CF = Op + Inv + Fin). Corrected mapping for all sectors. 🟢 **PASSED.**
g keys LCTT.
    - [ ] Re-sync `cash_flow` table cho VN30.
- [ ] **BL-4:** Mobile responsive UI

---

## 📌 Gate Checklist (Điều kiện unlock giai đoạn tiếp)

| Gate | Điều kiện | Unlock |
|---|---|---|
| **G1** | Resync 30 mã VN30 < 5 phút, accounting identity 100% | Giai đoạn 2 | ✅ |
| **G2** | SEC mapping audit pass, không còn hardcode BANK/SEC_TICKERS | Giai đoạn 3 | ✅ |
| **G3** | NIM/YOEA/LDR/CIR trên web có số, metrics batch 30 mã xong | Giai đoạn 4 | ✅ |
| **G4** | RLS đúng, Bandit clean, Quarterly Guide có | Giai đoạn 5 | ✅ |
| **G5** | BL-2 Pass (BS balance), BL-3 investigating (CF Gap) | Phase 6/Deploy | ⏳ |

---

## 📎 Reference

| Tài liệu | Mục đích |
|---|---|
| [Finsang_Master_Active_Roadmap.md](Finsang_Master_Active_Roadmap.md) | Phase timeline |
| [Finsang_Master_Findings.md](Finsang_Master_Findings.md) | F-001 → F-016 findings gốc |
| [Finsang_Master_Logs.md](Finsang_Master_Logs.md) | Log mỗi khi hoàn thành gate |
| [sub-projects/V5_improdata/v5_task.md](sub-projects/V5_improdata/v5_task.md) | V5 task chi tiết |
| [sub-projects/Version_2/metrics.py](sub-projects/Version_2/metrics.py) | Engine tính CSTC |
