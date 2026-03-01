# 📋 V3 Task Tracker — Simply Wall St Integration

> **Last Updated**: 2026-03-01 23:57 (GMT+7)
> **Plan file**: `v3_implementation_plan.md` (cùng thư mục)
> **Changelog**: `v3_changelog.md`

---

## ✅ V3.0 — Đã hoàn thành (Phase 1-4)

### Phase 1: Backend Data Layer
- [x] P1.1: `fetch_ohlcv_vn30.py` — 9,455 rows (31 tickers)
- [x] P1.2: `fetch_company_overview.py` — 30+ metrics per ticker via vnstock
- [x] P1.3: Supabase migrations (4 migrations: create table, extend cols, add missing cols, RLS)
- [x] P1.4: `calc_snowflake.py` — 5-dim scoring (Value/Future/Past/Health/Dividend)
- [x] P1.5: ROE/ROA/D/E tính trong Snowflake (không cần sửa metrics.py)

### Phase 2: Frontend Components
- [x] P2.0: Thêm tab "360 Overview" vào `App.jsx`
- [x] P2.1: `OverviewTab.jsx` — container component
- [x] P2.2: `CompanyHero.jsx` — giá, vốn hóa, sector badge
- [x] P2.3: `SnowflakeChart.jsx` — Pure SVG 5-axis radar
- [x] P2.4: `ValuationGauge.jsx` — CSS gradient P/E gauge
- [x] P2.5: `ChecklistCards.jsx` — sector-aware pass/fail (bank/sec/normal)
- [x] P2.6: `PriceChart.jsx` — Pure SVG area chart + hover tooltip
- [x] P2.7: `QuickStats.jsx` — 2×4 metric grid
- [x] P2.8: `useOverviewData.js` — 3 Supabase queries (overview, OHLCV, ratios)

### Phase 3: SWS Theme
- [x] P3.1: CSS variables from `theme.css`
- [x] P3.2: 420+ lines CSS styling for 360 tab
- [x] P3.3: Inter font imported

### Phase 4: Verification
- [x] P4.1: Data verification (31 tickers, non-null scores)
- [x] P4.2: Browser tests (VHC/VCB/SSI, all 5 tabs)
- [x] P4.3: CTO audit (RLS, no API key leaks, error handling)
- [x] P4.4: CFO validation (P/E, ROE, Snowflake sanity)

---

## ❌ V3.1 — Bổ sung tính năng (Phase 5-7)

### Phase 5: Financial Health Deep-Dive 🔴 PRIORITY 1

> **Agent gợi ý**: Frontend + Data Agent
> **Skills cần dùng**: `professional-cfo-analyst`, `kpi-dashboard-design`
> **Đọc trước**: `v3_implementation_plan.md` → mục "V3.1 Enhancement Plan → Phase 5"
> **Hướng dẫn agent**:
> 1. Đọc `v3_implementation_plan.md` section Phase 5 để hiểu specs
> 2. Đọc `frontend/src/components/ChecklistCards.jsx` để hiểu pattern hiện tại
> 3. Đọc `frontend/src/hooks/useOverviewData.js` để hiểu data flow
> 4. KHÔNG đọc toàn bộ App.jsx hoặc backend → tốn token thừa

- [ ] **P5.1**: `BankKeyInfo.jsx` — Key Information box chuyên biệt theo sector
  - Bank: Asset/Equity ratio, NIM, Total deposits, Loan/Deposit, Bad loans, Allowance
  - Normal: D/E, Current Ratio, Total Debt/Equity, Interest Coverage, Cash
  - Cần data: `company_overview` table (columns NIM, NPL... → xem P7.1)
  - **Blocked on**: P7.1 (bank metrics chưa có trong DB)

- [ ] **P5.2**: `FinancialPositionChart.jsx` — Stacked Bar (Assets vs Liabilities)
  - Pure SVG stacked bars: Short-term/Long-term Assets ↔ Liabilities + Equity
  - Data source: `balance_sheet_wide` table → extract `cdkt_tsnh`, `cdkt_tsdh`, `cdkt_nnh`, `cdkt_ndh`, `cdkt_vcsh`
  - **Blocked on**: P7.2 (cần view/cache BS summary)

- [ ] **P5.3**: `DebtEquityHistoryChart.jsx` — Line+Area trend chart 5-10 năm
  - Dual line (Debt = red, Equity = blue) with area fill
  - Data source: `balance_sheet_wide` → `cdkt_npt` + `cdkt_vcsh` historical periods
  - **Blocked on**: P7.2

- [ ] **P5.4**: Expandable Checklist Cards
  - Thêm `narrative` field + expand/collapse animation vào `ChecklistCards.jsx`
  - Thêm icon row summary header (✅❌✅✅✅✅ giống SWS)
  - **Không bị block** — có thể làm ngay

### Phase 6: Multi-Section 360 Tab Layout 🟡 PRIORITY 2

> **Agent gợi ý**: Frontend Agent
> **Skills cần dùng**: `ui-ux-pro-max`, `frontend-design`
> **Đọc trước**: `v3_implementation_plan.md` → mục "Phase 6"
> **Hướng dẫn agent**:
> 1. Đọc `frontend/src/components/OverviewTab.jsx` (133 lines) để hiểu layout hiện tại
> 2. Thêm section anchors + sticky sub-nav bar
> 3. KHÔNG tách ra pages riêng — giữ nguyên single-tab structure

- [ ] **P6.1**: Section-Based Navigation (internal anchors: Summary / Valuation / Health / History / Dividend)
  - `scrollIntoView({ behavior: 'smooth' })` on click
  - CSS: `.section-nav` sticky bar xám nhạt
  - **Blocked on**: P5.x components phải xong trước

- [ ] **P6.2**: Checklist Header Icon Row
  - `Financial Health criteria checks 5/6  ✅ ❌ ✅ ✅ ✅ ✅  [→]`
  - Mở rộng `ChecklistCards.jsx`
  - **Blocked on**: P5.4

### Phase 7: Data Pipeline Enhancement 🟢 PRIORITY 3 (nhưng cần chạy trước P5)

> **Agent gợi ý**: Data Engineer / Backend Agent
> **Skills cần dùng**: `data-engineering-data-pipeline`, `professional-cfo-analyst`
> **Đọc trước**: `V3_SimplyWallSt/scripts/fetch_company_overview.py` (hiểu pattern upsert)
> **Hướng dẫn agent**:
> 1. Chạy P7.1 TRƯỚC tiên vì P5.1 cần data
> 2. Dùng MCP tool `apply_migration` cho SQL migrations
> 3. Test với `--dry-run` trước khi upsert thật
> 4. Delay 1.0s giữa các tickers để tránh rate limit từ VCI

- [ ] **P7.1**: Fetch Bank-Specific Metrics (NIM, NPL, Loan/Deposit, Financial Leverage)
  - Mở rộng `fetch_company_overview.py` hoặc tạo script mới
  - Migration: Thêm 7 columns vào `company_overview`
  - **PHẢI LÀM TRƯỚC P5.1**

- [ ] **P7.2**: Historical Balance Sheet Summary View
  - Tạo Supabase view `balance_sheet_summary` cho D/E History chart
  - Hoặc: query trực tiếp `balance_sheet_wide` từ frontend hook
  - **PHẢI LÀM TRƯỚC P5.2 và P5.3**

---

## 🗺️ Execution Order khuyến nghị

```
Bước 1: P7.1 (bank data migration + fetch)    → ~5K tokens
Bước 2: P7.2 (BS summary view)                → ~3K tokens
Bước 3: P5.4 (expandable checklists)          → ~5K tokens  ← có thể song song Bước 1-2
Bước 4: P5.1 (BankKeyInfo component)          → ~5K tokens
Bước 5: P5.2 + P5.3 (Position + D/E charts)   → ~8K tokens  ← song song
Bước 6: P6.1 + P6.2 (section nav + icons)     → ~8K tokens
Bước 7: Browser test toàn bộ                  → ~3K tokens
```

**Tổng ước tính**: ~37K tokens, 5-7 sessions
