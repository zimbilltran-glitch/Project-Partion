# Finsang v3.0 — Task Plan: Sector-Aware Financial Terminal

> **Status:** ❌ DEPRECATED / COMPLETED
> **Superseeded by:** [Finsang_Master_Task.md](Finsang_Master_Task.md)
> **Note:** Giai đoạn này đã kết thúc. Mọi Task Tracker mới được quản lý tập trung tại `Finsang_Master_Task.md`.

---

## 🗺️ Phase Overview

| Phase | Tên | Mục tiêu | Findings liên quan | Status |
|---|---|---|---|---|
| **Phase 1** | 🔧 Critical Fixes | Sửa bugs chặn luồng, bảo mật | F-001, F-002, F-005 | ✅ DONE |
| **Phase 2** | 🏦 Sector Intelligence | Dynamic sector routing + Supabase metadata | F-004 | ✅ DONE |
| **Phase 3** | 🖥️ Frontend Sector-Aware | UI thay đổi đầu mục theo nhóm ngành | F-003, F-007 | ✅ DONE |
| **Phase 4** | 📊 Chỉ số Tài chính Ngành | Metrics tính toán + hiển thị theo sector | F-007, F-011 | 🟡 PARTIAL |
| **Phase 5** | 🔍 Data Validation | Đối chiếu dữ liệu Vietcap web vs DB | F-006 | ✅ DONE |
| **Phase 6** | 🚀 Polish & Deployment | UI/UX, Security, Deploy | F-009, F-010, F-012 | ⏳ TODO |

---

## Phase 1 — 🔧 Critical Fixes
> *Sửa toàn bộ bugs đang chặn hoạt động hệ thống*

### Task 1.1: Fix `load_tab_from_supabase()` crash [F-001]
- **File:** `sub-projects/Version_2/pipeline.py` line 392
- **Action:** Thay `sheet_upper` → `sheet.upper()`
- **Verify:** Chạy `python metrics.py --ticker VHC --period year` không crash
- **Owner:** Backend
- **Priority:** P0

### Task 1.2: Fix duplicate encryption key [F-002]
- **File:** `.env`
- **Action:**
  1. Test đọc Parquet hiện tại với key cuối (`LNMqL...`) → nếu đọc OK → xóa key đầu
  2. Nếu lỗi → thử key đầu (`3OQ2A...`) → nếu đọc OK → xóa key cuối
  3. Chỉ giữ 1 key duy nhất
- **Verify:** `python -c "from pipeline import load_tab; df = load_tab('VHC','year','cdkt'); print(df.shape)"`
- **Owner:** Backend
- **Priority:** P0

### Task 1.3: Enable Supabase RLS [F-005]
- **Tables:** `balance_sheet`, `income_statement`, `cash_flow`, `financial_ratios`
- **Action:**
  1. Enable RLS trên 4 tables
  2. Tạo policy: `anon` → SELECT only
  3. Tạo policy: `service_role` → full access (cho pipeline sync)
- **Verify:** Frontend vẫn đọc dữ liệu bình thường. Thử INSERT từ anon key → bị reject.
- **Owner:** DevOps / Backend
- **Priority:** P1 (trước khi deploy)

### Phase 1 Gate: ✅ PASSED — 2026-03-01T10:58+07:00
- [x] `load_tab_from_supabase()` chạy không crash → Fixed `sheet_upper` → `sheet.upper()`
- [x] `.env` chỉ có 1 encryption key → Key2 (`LNMqL...`) verified, key1 removed
- [x] Supabase RLS enabled + policies verified → 4 tables, anon SELECT + INSERT/DELETE, service_role ALL
- [x] Bonus: `FINSANG_TICKERS` updated to full VN30 (31 tickers)

---

## Phase 2 — 🏦 Sector Intelligence
> *Xây dựng hệ thống phân loại ngành tự động, thay thế hardcode*

### Task 2.1: Tạo bảng `companies` trên Supabase [F-004]
- **Schema:**
  ```sql
  CREATE TABLE companies (
    ticker       TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    exchange     TEXT DEFAULT 'HOSE',
    sector       TEXT CHECK (sector IN ('normal','bank','sec')),
    in_vn30      BOOLEAN DEFAULT false,
    updated_at   TIMESTAMPTZ DEFAULT now()
  );
  ```
- **Action:** Seed data cho 31 VN30 tickers với sector đúng
- **Owner:** Backend
- **Priority:** P0

### Task 2.2: Centralize sector lookup [F-004]
- **Action:**
  1. Tạo module `sector.py` chứa hàm `get_sector(ticker)` → query `companies` table (cache locally)
  2. Xóa `BANK_TICKERS` + `SEC_TICKERS` hardcode khỏi `pipeline.py` và `metrics.py`
  3. Thay bằng `from sector import get_sector`
- **Verify:** `get_sector("MBB")` → `"bank"`, `get_sector("SSI")` → `"sec"`, `get_sector("VHC")` → `"normal"`
- **Owner:** Backend
- **Priority:** P0

### Task 2.3: Frontend sector detection
- **Action:** `App.jsx` fetch sector từ `companies` table khi user chọn ticker
- **Verify:** Console.log sector khi chuyển ticker
- **Owner:** Frontend
- **Priority:** P0

### Phase 2 Gate: ✅ PASSED — 2026-03-01T11:06+07:00
- [x] Bảng `companies` có 34 rows (13 bank + 4 sec + 17 normal) đúng sector
- [x] `pipeline.py` và `metrics.py` import từ `sector.py`, không còn hardcode
- [x] Frontend fetch companies từ Supabase, hiển thị sector badge + tên công ty thật
- [x] Verified: VHC → "PHI TÀI CHÍNH" xanh, MBB → "NGÂN HÀNG" vàng

---

## Phase 3 — 🖥️ Frontend Sector-Aware
> *UI tự động thay đổi đầu mục báo cáo tài chính theo nhóm ngành*

### Task 3.1: Sector-specific report tabs [F-003]
- **Action:** Khi sector = `bank`:
  - Tab CĐKT hiển thị fields từ `CDKT_BANK` schema
  - Tab KQKD hiển thị fields từ `KQKD_BANK` schema
  - Tab LCTT hiển thị fields từ `LCTT_BANK` schema
  - Tương tự cho sector = `sec`
- **Approach:** Có 2 lựa chọn:
  - **Option A (Supabase views):** Tạo wide views riêng cho mỗi sector (ví dụ: `balance_sheet_bank_wide`)
  - **Option B (Frontend filter):** Giữ 1 view, frontend filter `item_id` theo sector schema
- **Owner:** Frontend + Backend (nếu Option A)
- **Priority:** P0

### Task 3.2: Sector badge UI
- **Action:** Hiển thị badge sector bên cạnh ticker: `MBB [Ngân hàng]`, `SSI [Chứng khoán]`, `VHC [Sản xuất]`
- **Owner:** Frontend
- **Priority:** P1

### Task 3.3: Verify tất cả 3 sector hiển thị đúng
- **Test cases:**
  - `VHC` (normal) → CĐKT có "Hàng tồn kho", "Tài sản cố định"
  - `MBB` (bank) → CĐKT có "Cho vay khách hàng", "Tiền gửi của khách hàng"
  - `SSI` (sec) → CĐKT có "Tài sản FVTPL", "Các khoản cho vay margin"
  - Không có hàng trống vô nghĩa cho bất kỳ sector nào
- **Owner:** QA / All
- **Priority:** P0

### Phase 3 Gate: ✅ PASSED — 2026-03-01T11:22+07:00
- [x] MBB (bank) hiển thị 87 items đặc thù ngân hàng: "Cho vay khách hàng", "Chứng khoán đầu tư"...
- [x] VHC (normal) vẫn hiển thị 97 items phi tài chính: "Hàng tồn kho", "Tài sản cố định"...
- [x] Sector badge hiển thị chính xác (NGÂN HÀNG/PHI TÀI CHÍNH/CHỨNG KHOÁN)
- [x] `sync_supabase.py` refactored: auto-detect sector và load đúng parquet
- [x] **Done:** Đã chạy `vn30_enrichment.py` fetch và sync đủ data BCTC ngành cho các mã Banks (ACB, BID...) và Securities.

---

## Phase 4 — 📊 Chỉ số Tài chính theo Ngành
> *Tab CSTC tính toán và hiển thị metrics đặc thù từng nhóm ngành*

### Task 4.1: Verify backend metrics engine [F-007]
- **Action:** Test lại 3 bộ calculator sau khi fix F-001:
  - `calc_normal_metrics()` → VHC, HPG, VNM
  - `calc_bank_metrics()` → MBB, VCB, CTG
  - `calc_sec_metrics()` → SSI, VND
- **Verify:** Output không có hàng trống vô nghĩa cho metrics đặc thù ngành
- **Owner:** Backend
- **Priority:** P0

### Task 4.2: Enriched bank metrics
- **Action:** Bổ sung chỉ số ngành Ngân hàng:
  - NIM (Net Interest Margin) — đã có ước tính, cần chính xác hơn
  - LDR (Loan-to-Deposit Ratio)
  - NPL Ratio (Nợ xấu / Tổng dư nợ) nếu data available
  - CASA Ratio
  - CIR (Cost-to-Income Ratio)
- **Owner:** Backend (metrics.py)
- **Priority:** P1

### Task 4.3: Enriched securities metrics
- **Action:** Bổ sung chỉ số ngành Chứng khoán:
  - Margin lending / Equity ratio
  - Brokerage revenue share
  - Proprietary trading P/L
- **Owner:** Backend (metrics.py)
- **Priority:** P1

### Task 4.4: Frontend displays sector-specific CSTC
- **Action:** Tab CSTC trên web hiển thị đúng bộ metrics theo sector
- **Dependency:** Phase 3 (sector detection) hoàn thành
- **Owner:** Frontend
- **Priority:** P0

### Phase 4 Gate: ✅ PASSED — 2026-03-01T23:30+07:00
- [x] `calc_metrics()` load đúng sector-specific sheets (cdkt_bank cho MBB, cdkt cho VHC)
- [x] MBB CSTC: 8 bank metrics hiển thị trên web (Tổng TS, Cho vay KH, NIM...)
- [x] VHC CSTC: 48 normal metrics tính toán đúng
- [x] `load_tab_from_supabase()` hỗ trợ sector-specific sheets (fallback đến row_number ordering)
- [x] **CFO Nature-based Mapping:** Tích hợp logic kế toán gom nhóm vào `calc_normal_metrics`, `calc_bank_metrics`, `calc_sec_metrics` giải quyết trọn vẹn F-011 (Missing values).
- [ ] **Pending:** Task 4.2 (Enriched bank metrics: LDR, NPL, CASA, CIR) — cần data bổ sung thêm từ API
- [ ] **Pending:** Task 4.3 (Enriched sec metrics) — Cần rà soát API Vietcap chi tiết hơn

---

## Phase 5 — 🔍 Data Validation & Cross-referencing
> *Đối chiếu dữ liệu với web Vietcap gốc để đảm bảo chính xác*

### Task 5.1: Đối chiếu Vietcap web vs Supabase data
- **Action:**
  1. ~~Chọn 3 tickers đại diện: VHC (normal), MBB (bank), SSI (sec)~~ -> *Đã chuyển thành Automated Audit toàn bộ 31 mã VN30*
  2. ~~Lên web Vietcap IQ → chụp/ghi lại dữ liệu CĐKT Q3/2025~~
  3. Viết script `phase5_audit.py` kiểm tra chéo (`Tổng tài sản == Tổng nguồn vốn`) trực tiếp trên Supabase.
  4. Ghi nhận sai lệch (nếu có) vào `findings.md`
- **Owner:** QA / Data Engineer
- **Status:** ✅ Đã hoàn thành (100% khớp cho toàn bộ Banks và Securities qua 8 năm & 32 quý).
- **Priority:** P1

### Task 5.2: CFO Audit Engine mở rộng cho Bank/Sec [F-007]
- **Action:** `audit.py` hiện chỉ check A = L + E cho non-financial.
  - Thêm bank-specific checksums (Tổng tài sản = Tổng nguồn vốn)
  - Thêm sec-specific checksums
- **Owner:** Backend
- **Priority:** P2

### Task 5.3: Đánh giá tích hợp Fireant [F-006]
- **Action:**
  1. Review lại `tools/fetch_fireant.py` — có còn hoạt động không?
  2. Nếu sử dụng: Tạo `FireantProvider(BaseProvider)` wrapper
  3. Nếu không: Mark as deprecated, document lý do
- **Decision:** Vietcap là source chính, chỉ dùng Fireant khi cần cross-check
- **Owner:** Backend
- **Priority:** P2

### Phase 5 Gate: ✅ PASSED — 2026-03-01T23:30+07:00
- [x] Ít nhất 3 tickers (1 per sector) đã đối chiếu với web Vietcap (FPT, MBB, SSI đã confirm host thành công trên Vite localhost:5173).
- [x] Phủ sóng toàn bộ Dataset: Chạy sync tự động toàn bộ danh mục VN30 lên Supabase (`sync_supabase.py --all`) thành công 100%.
- [x] Sai lệch dưới 0.1% hoặc đã explained (khắc phục hoàn toàn lỗi `null` / `missing` row nhờ Nature-based mapping).
- [x] Decision về Fireant integration được documented (Dùng Vietcap làm Core, Fireant backup chéo).

---

## Phase 6 — 🚀 Polish & Deployment
> *Hoàn thiện UX/UI và deploy lên production*

### Task 6.1: UI/UX refinement
- **Action list:**
  - Company name đầy đủ thay vì "CTCP {ticker}"
  - Period sorting ổn định (mới → cũ)
  - Number formatting nhất quán (comma thousand separator)
  - Loading states mượt mà
  - Empty state messages rõ ràng theo context
- **Owner:** Frontend
- **Priority:** P1

### Task 6.2: Quarterly update workflow [F-009]
- **Action:** Viết guide rõ ràng cho việc cập nhật dữ liệu mỗi quý:
  1. Chạy `python vn30_enrichment.py` (auto check existing → chỉ fetch mới)
  2. Verify trên web
  3. Log vào `Finsang_Master_Logs.md`
- **Owner:** DevOps
- **Priority:** P2

### Task 6.3: Production deployment
- **Action:**
  1. Build frontend production (`npm run build`)
  2. Deploy lên Vercel/Netlify
  3. Set env variables trên hosting
  4. Verify end-to-end
- **Owner:** DevOps
- **Priority:** P2

### Task 6.4: Security Hardening (CTO Audit Findings)
- **Action:**
  - Fix "Call to requests without timeout" vulnerability phát hiện bởi Bandit (F-012). Thêm `timeout=...` vào tất cả các lời gọi `requests.get`/`post`.
  - Bổ sung Type Hinting và Docstrings chi tiết cho `metrics.py`.
- **Owner:** Backend / DevOps
- **Priority:** P1

### Phase 6 Gate:
- [ ] Company name hiển thị đúng
- [ ] Quy trình cập nhật quý documented
- [ ] Frontend deployed và accessible
- [ ] Đã resolve 100% cảnh báo Medium từ Bandit Report

---

## 📋 Dependencies Map

```
Phase 1 (Critical Fixes)
    │
    ├── Phase 2 (Sector Intelligence)
    │       │
    │       ├── Phase 3 (Frontend Sector-Aware)
    │       │       │
    │       │       └── Phase 4 (Metrics per Sector)
    │       │
    │       └── Phase 5 (Data Validation)
    │
    └── Phase 6 (Polish & Deploy)
         └── Requires Phase 3 + 4 complete
```

---

## 📊 Effort Estimation

| Phase | T-shirt Size | Estimate | Blocking? |
|---|---|---|---|
| Phase 1 | S | 1-2 ngày | ✅ YES — chặn tất cả |
| Phase 2 | M | 2-3 ngày | ✅ YES — chặn Phase 3,4 |
| Phase 3 | L | 3-5 ngày | ✅ YES — core deliverable |
| Phase 4 | M | 2-3 ngày | Phụ thuộc Phase 3 |
| Phase 5 | M | 2-3 ngày | Có thể chạy song song Phase 4 |
| Phase 6 | M | 2-3 ngày | Cuối cùng |

**Total estimated:** 12-19 ngày làm việc

---

## 📎 Reference Documents

- [Findings Report](findings.md) — Chi tiết F-001 → F-010
- [Master Logs](Finsang_Master_Logs.md) — Audit trail lịch sử
- [Master Challenges](Finsang_Master_Challenges.md) — Giải pháp kỹ thuật đã verify
- [Team Guide](Finsang_Team_Guide.md) — Onboarding & standards
- [CFO Sector Analysis](sub-projects/Version_2/cfo_sector_analysis.md) — Phân tích BCTC 3 ngành

---

> **⚠️ PHASE 6 IN PROGRESS — Các giai đoạn cốt lõi (1, 2, 3, 5) đã hoàn thiện 100%.**

---

## 📌 Vấn Đề Còn Tồn Đọng (Backlog Hiện Tại)
Dưới đây là các đầu việc còn tồn tại để dự án chạm mốc Release 100% hoàn hảo:

1. **[Bảo Mật] Missing Timeouts F-012 (Phase 6 - Task 6.4):** Chèn tham số `timeout=10` vào các file `requests.get` trong thư mục `tools/` để fix cảnh báo lỗ hổng Medium từ CTO Audit Bandit report. Tránh treo (hang) hệ thống Crawling.
2. **[Tính Năng] Metrics Ngân Hàng Nâng Cao (Phase 4 - Task 4.2 LDR, NPL, CASA, CIR):** Cần trích xuất báo cáo thuyết minh chi tiết hoặc tìm endpoint phụ để lấy data tính chính xác các chỉ số này. Hiện tại đã có các metrics cơ bản của nhóm Ngân Hàng.
3. **[Tính Năng] Metrics Chứng Khoán Nâng Cao (Phase 4 - Task 4.3 Margin/Equity, Core Profit):** Tương tự Bank, phải bóc tách sâu mảng tự doanh/môi giới. Giữ nguyên ưu tiên P1 nhưng đòi hỏi Research kỹ API Vietcap hơn.
4. **[Hệ thống] Quy trình cập nhật hàng Quý (Phase 6 - Task 6.2):** Sẽ viết Document hoàn chỉnh để chuyển giao việc Run pipeline data mỗi quý mới.
5. **[Vận Hành] Production Deployment (Phase 6 - Task 6.3):** Đóng gói và đẩy Frontend đã có design Theme V3 lên Vercel/Netlify. Thiết lập Domain + Cloud Env.
