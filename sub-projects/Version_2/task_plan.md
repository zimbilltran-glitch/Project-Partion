# Finsang B.L.A.S.T. Execution Plan — Vietcap Migration

> **Version:** 2.0 | **Date:** 2026-02-24 | **Status:** 🟡 AWAITING APPROVAL
> **Primary Source:** [Vietcap IQ](https://trading.vietcap.com.vn/iq/company?ticker=VHC)
> **Golden Schema:** `VHC_BCTC.xlsx` (4 sheets — Quarter/Year × CĐKT/KQKD/LCTT/CSTC)
> **Supersedes:** `task_plan.md` v1.0 (KBSV / vnstock era)

---

## 🗺️ Skill Register (Phân quyền Đội ngũ)

| # | Skill / Role | Responsibility in this Pipeline |
|---|---|---|
| 🎯 | `@product-manager-toolkit` | **Orchestrator** — PRD, RICE score, scope gate at each phase |
| 📐 | `@data-engineer` | Schema design, ETL strategy, Parquet partition architecture |
| 🕷️ | `@autonomous-web-scraper` | Executes extraction (API intercept **or** headless Excel download) |
| 🔄 | `@financial-data-normalizer` | Maps raw payload → Golden Schema (VHC_BCTC 4-sheet standard) |
| 📊 | `@data-scientist` | Statistical validation, derived metrics (YoY, margins, ratios) |
| 💼 | `@professional-cfo-analyst` | Final audit — checksum, accounting identity (A = L + E) |
| 🎨 | `@ui-ux-designer` + `@ui-ux-pro-max` | Terminal/Markdown tabbed layout mimicking Vietcap's Quarter/Year tabs |
| 🏛️ | `@cto-mentor-supervisor` | Architectural review — production readiness, anti-over-engineering |

---

## Phase 1 — 🔵 BLUEPRINT
> *Define requirements, investigate extraction strategy, map the Golden Schema*

### 1.1 `@product-manager-toolkit` — Product Requirements

**Epic:** "As a financial analyst, I can switch between Quarter/Year tabs for any ticker to view CĐKT, KQKD, LCTT, and CSTC — identical to the Vietcap IQ interface."

**User Stories (RICE Prioritized):**

| Story | R | I | C | E | Score |
|---|---|---|---|---|---|
| View KQKD by Quarter (latest 8Q) | 9 | 9 | 3 | 1.0 | **27** |
| View CĐKT by Year (latest 5Y) | 8 | 8 | 3 | 1.0 | **21** |
| Switch between tabs (Q ↔ Y) | 9 | 9 | 2 | 1.0 | **40** |
| Search by ticker symbol | 7 | 7 | 2 | 0.8 | **24** |
| Download raw Excel (Golden Schema) | 5 | 4 | 2 | 0.6 | **10** |

**In-Scope:** VHC as pilot ticker → any VN ticker.
**Out-of-Scope:** Real-time prices, trading signals, portfolio management.

**Acceptance Criteria (Phase Gate):**
- [ ] PRD signed off by PM
- [ ] VHC_BCTC.xlsx fully parsed and schema documented
- [ ] Extraction method decided (API vs. Excel) with rationale

---

### 1.2 `@data-engineer` — Extraction Strategy Investigation

**Decision Matrix: API Interception vs. Headless Excel Download**

| Criterion | API Interception | Excel Download |
|---|---|---|
| **Stability** | 🟡 Medium (headers may rotate) | 🟢 High (file download is stable) |
| **Data Fidelity** | 🟢 Exact JSON → direct mapping | 🟢 Excel = Golden Schema format |
| **Speed** | 🟢 Fast (no parse overhead) | 🟡 Medium (Playwright + openpyxl) |
| **Rate-limit Risk** | 🔴 High (per-request token) | 🟡 Medium (file-level throttle) |
| **Maintenance** | 🔴 Breaks on endpoint change | 🟡 Breaks on layout change |
| **Golden Schema alignment** | 🔴 Requires full custom mapping | 🟢 Native alignment |

> **Recommended Decision (pending PM gate):**
> **Primary → API Interception** (Vietcap internal JSON endpoints — fastest, lowest resource usage)
> **Fallback → Excel Download** via headless Playwright (triggered only if API tokens rotate or endpoints break)

**Tasks:**
- [ ] Capture Vietcap IQ network requests via DevTools for VHC → document all JSON endpoints + auth headers
- [ ] Verify token refresh mechanism and session lifetime for API access
- [ ] Map Excel download trigger as documented fallback path
- [ ] Prototype API interception approach in isolation (no pipeline yet)

---

### 1.3 `@financial-data-normalizer` — Golden Schema Analysis

**Source:** `VHC_BCTC.xlsx` — 4 sheets:

| Sheet | Vietnamese Name | English Equivalent | Key Metrics |
|---|---|---|---|
| `CDKT` | Cân Đối Kế Toán | Balance Sheet | Total Assets, Total Liabilities, Equity |
| `KQKD` | Kết Quả Kinh Doanh | Income Statement | Revenue, COGS, Gross Profit, Net Profit |
| `LCTT` | Lưu Chuyển Tiền Tệ | Cash Flow Statement | Operating CF, Investing CF, Financing CF |
| `CSTC` | Chỉ Số Tài Chính | Financial Ratios | EPS, P/E, ROE, ROA, D/E |

**Tasks:**
- [ ] Parse VHC_BCTC.xlsx → extract all row labels, units, and value types per sheet
- [ ] Create `golden_schema.json` — canonical field registry (field_id, vn_name, en_name, unit, data_type)
- [ ] Flag any fields present in Vietcap output but absent from Golden Schema

**Phase 1 Gate (PM sign-off required before Phase 2):**
- [ ] Extraction strategy confirmed (API or Excel)
- [ ] `golden_schema.json` finalized
- [ ] Endpoint/download mechanism documented

---

## Phase 2 — 🟣 LINK
> *Scraper connects to Vietcap using Data Engineer specifications*

### 2.1 `@autonomous-web-scraper` — Vietcap Connection

**Input:** Extraction spec from Phase 1 (endpoint map OR download trigger path)

**Tasks (API Interception — PRIMARY):**
- [ ] Intercept `Authorization` bearer token from Vietcap IQ login session
- [ ] Map all BCTC JSON endpoints (CDKT/KQKD/LCTT/CSTC) per period type (quarter/year)
- [ ] Parametrize requests: `?ticker={TICKER}&period=quarter&limit=8` and `&limit=10` for year
- [ ] Save raw JSON responses to `.tmp/raw/{TICKER}/` with timestamp
- [ ] Verify response integrity (non-empty payload, expected field keys present)

**Tasks (Excel Download — FALLBACK, trigger only on API failure):**
- [ ] Launch headless Playwright → navigate to `https://trading.vietcap.com.vn/iq/company?ticker={TICKER}`
- [ ] Click "Tải về" (Download) button for each financial tab
- [ ] Save downloaded `.xlsx` to `.tmp/raw/{TICKER}/` with timestamp
- [ ] Verify file integrity (non-zero size, valid XLSX header)
- [ ] Log fallback activation to `pipeline_runs.extraction_method = 'excel_fallback'`

**Phase 2 Gate:**
- [ ] Raw VHC data successfully retrieved and saved to `.tmp/`

- [ ] At minimum 8 quarters + 10 years of data available

- [ ] No rate-limit blocks encountered in test run

---

## Phase 3 — 🟠 ARCHITECT
> *Build the full data pipeline, storage layer, and validation rules*

### 3.1 `@data-engineer` — Parquet Hive-Style Pipeline

**Storage Architecture:**
```
data/
└── financial/
    └── {ticker}/
        └── period_type={quarter|year}/
            └── sheet={cdkt|kqkd|lctt|cstc}/
                └── {ticker}_{period}.parquet
```

**Pipeline Flow:**
```
.tmp/raw/{TICKER}/*.json  (or *.xlsx if fallback)
        ↓ (requests / pandas read_excel)
   Raw DataFrame
        ↓ (financial-data-normalizer)
   Normalized DataFrame (Golden Schema)
        ↓ (pandas to_parquet, Hive-partitioned)
   data/financial/{ticker}/.../*.parquet
        ↓ 🗑️ GARBAGE COLLECTION (auto-delete .tmp/raw/{TICKER}/*)
        ↓ (pyarrow filtered read)
   In-memory DataFrame → UI render
        ↓ (supabase-py upsert)
   Supabase → metadata + pipeline_runs
```

**Supabase Metadata Schema:**
```sql
CREATE TABLE pipeline_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  period_type TEXT CHECK (period_type IN ('quarter', 'year')),
  sheet TEXT CHECK (sheet IN ('cdkt', 'kqkd', 'lctt', 'cstc')),
  periods_fetched TEXT[],
  source TEXT DEFAULT 'vietcap',
  extraction_method TEXT,
  run_at TIMESTAMPTZ DEFAULT now(),
  status TEXT DEFAULT 'success',
  error_log TEXT
);

CREATE TABLE financial_fields (
  field_id TEXT PRIMARY KEY,
  vn_name TEXT NOT NULL,
  en_name TEXT,
  sheet TEXT,
  unit TEXT,
  data_type TEXT DEFAULT 'DECIMAL'
);
```

**Tasks:**
- [ ] Build `pipeline.py` — orchestrates Extract → Normalize → Store → GC
- [ ] Implement Parquet writer with Hive partitioning
- [ ] Build `load_tab(ticker, period_type, sheet)` → returns filtered DataFrame
- [ ] Upsert `pipeline_runs` on each run
- [ ] **Garbage Collection:** Implement `cleanup_tmp(ticker)` — auto-deletes all files under `.tmp/raw/{ticker}/` immediately after successful Parquet write is confirmed. On failure, files are retained for debugging and logged to `pipeline_runs.error_log`.

---

### 3.2 `@data-scientist` — Derived Metrics & Validation Rules

**Derived Metrics:**

| Metric | Formula | Sheet |
|---|---|---|
| Gross Margin % | `gross_profit / revenue * 100` | KQKD |
| Net Margin % | `net_profit / revenue * 100` | KQKD |
| YoY Revenue Growth | `(rev_t - rev_t1) / rev_t1 * 100` | KQKD |
| QoQ Net Profit Δ | `(np_t - np_t1) / abs(np_t1) * 100` | KQKD |
| Current Ratio | `current_assets / current_liabilities` | CĐKT |
| D/E Ratio | `total_debt / total_equity` | CĐKT |
| Free Cash Flow | `operating_cf - capex` | LCTT |

**Validation Rules:**
- [ ] No null values in core fields for fetched periods
- [ ] Revenue > 0 for operating companies
- [ ] Time-series continuity: no gap > 1 quarter between periods
- [ ] Ratios within plausible sector bounds (flag outliers, don't reject)

---

### 3.3 `@professional-cfo-analyst` — Financial Audit Rules

**Accounting Identity Checks:**
```
Total Assets = Total Liabilities + Total Equity  (tolerance: ±0.1%)
Net CF = Operating CF + Investing CF + Financing CF
EPS = Net Profit / Diluted Shares Outstanding
```

**Audit Outputs:**
- `PASS` — proceeds to UI
- `WARN` — displayed with ⚠️ flag
- `FAIL` — pipeline halted, error logged to `pipeline_runs.error_log`

**Phase 3 Gate:**
- [ ] Parquet pipeline runs end-to-end for VHC (all 4 sheets, Q+Y)
- [ ] Scientist validation passes (no critical nulls)
- [ ] CFO audit: accounting identity PASS for all periods

---

## Phase 4 — 🟡 STYLIZE
> *Design the tabbed terminal/Markdown UI mimicking Vietcap IQ*

### 4.1 `@ui-ux-designer` + `@ui-ux-pro-max` — Presentation Layer

**Vietcap Tab Structure to Replicate:**
```
[ Quý ]  [ Năm ]                          ← Period Type Tabs
[ CĐKT ] [ KQKD ] [ LCTT ] [ CSTC ]      ← Sheet Tabs
```

**Sample Terminal Output:**
```
═══════════════════════════════════════════════════════════
  FINSANG — VHC  |  Kết Quả Kinh Doanh (KQKD)
  Chế độ: ▶ QUÝ  |  Năm
═══════════════════════════════════════════════════════════
  Chỉ tiêu              │ Q4/24 │ Q3/24 │ Q2/24 │ Q1/24 │ …
  ─────────────────────────────────────────────────────────
  Doanh thu thuần       │ 2,450 │ 2,210 │ 1,980 │ 2,100 │
  Lợi nhuận gộp         │   612 │   552 │   495 │   525 │
  Biên lợi nhuận gộp %  │ 25.0% │ 25.0% │ 25.0% │ 25.0% │
  Lợi nhuận sau thuế    │   245 │   210 │   188 │   198 │
═══════════════════════════════════════════════════════════
  ▲ YoY: +12.3%  │  QoQ: +16.7%  │  Audit: ✅ PASS
```

**Design Rules:**
- [ ] Newest → oldest columns (left to right)
- [ ] 8 quarters OR 5 years per view
- [ ] Thousands separator: `,` | Negative: `()` or `–`
- [ ] Trend icons `▲ ▼ ─` next to key metrics
- [ ] CFO audit badge `✅/⚠️/❌` in footer
- [ ] Tab state persisted within session

**Phase 4 Gate:**
- [ ] UI renders correctly for VHC Q and Y views across all 4 sheets
- [ ] All design rules satisfied

---

## Phase 5 — 🔴 TRIGGER
> *End-to-end test with a new ticker; CTO architectural review*

### 5.1 Integration Test — Ticker: `FPT`

- [ ] Scraper downloads FPT BCTC from Vietcap
- [ ] Normalizer maps FPT to Golden Schema (log new fields)
- [ ] Parquet files created at correct Hive paths
- [ ] Scientist validation: no critical nulls, continuous time-series
- [ ] CFO audit: accounting identity PASS
- [ ] UI renders all 4 tabs (Q+Y) for FPT
- [ ] `pipeline_runs` row in Supabase: `status = 'success'`

### 5.2 `@cto-mentor-supervisor` — Production Readiness Review

- [ ] Pipeline is idempotent (re-run = no duplicates)
- [ ] All failure modes log gracefully to `pipeline_runs`
- [ ] No secrets hardcoded (`.env` for all keys)
- [ ] Parquet read < 2s for 8-quarter load
- [ ] Extraction fallback path documented
- [ ] Complexity ≤ 3 Python files for core pipeline
- [ ] README updated with architecture diagram + quickstart
- [ ] CTO readiness score ≥ 80/100

---

## 📋 Phase Summary

| Phase | Name | Lead Skill | Output | Status |
|---|---|---|---|---|
| **B** | Blueprint | PM + Data Eng + Normalizer | PRD, `golden_schema.json`, extraction decision | ⬜ Pending |
| **L** | Link | Scraper | Raw `.xlsx` / JSON in `.tmp/` | ⬜ Pending |
| **A** | Architect | Data Eng + Scientist + CFO | Parquet pipeline, Supabase schema, audit rules | ⬜ Pending |
| **S** | Stylize | UI/UX + UI-Pro-Max | Formatted tabbed output | ⬜ Pending |
| **T** | Trigger | All (CTO reviews) | E2E pass on `FPT`, CTO sign-off | ⬜ Pending |

---

> **⚠️ HOLD — Awaiting USER approval before Phase 1 begins.**
