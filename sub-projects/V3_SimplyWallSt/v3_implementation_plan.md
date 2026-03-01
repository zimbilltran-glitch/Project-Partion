# 🎯 Finsang V3 — Simply Wall St 360° Overview
# B.L.A.S.T. Implementation Plan

> **Blueprint → Layer → Assemble → Style → Test**  
> **Date**: 2026-03-01 | **Version**: 1.0 (Final - 100% Complete)  
> **Supabase Project**: `zuphshdgudnwlfjlfbbs`  
> **Frontend**: `Finsang/frontend/` (Vite + React 19, Vanilla CSS)  
> **Backend**: `Finsang/sub-projects/Version_2/`  
> **This file**: `Finsang/sub-projects/V3_SimplyWallSt/implementation_plan.md`

---

## 📌 Tổng quan dự án

### Mục tiêu
Thêm tab **"360 Overview"** vào Finsang frontend, lấy cảm hứng từ Simply Wall St.  
Tab mới chứa: Snowflake radar chart, P/E valuation gauge, checklist cards, stock price chart.  
**Giữ nguyên** 4 tabs hiện tại (CDKT, KQKD, LCTT, CSTC).

### Quyết định kiến trúc (User-confirmed)

| Quyết định | Lựa chọn | Lý do |
|---|---|---|
| Chart library | **Plotly.js** | Chạy native cả Vite (react-plotly.js) và Streamlit (st.plotly_chart) |
| Valuation model | **P/E based** | Đã có OHLCV data, đơn giản & chính xác |
| Tab structure | **Thêm "360 Overview"** | Giữ nguyên 4 tabs cũ, VN market friendly |
| OHLCV scope | **VN30, 2025-2026** | Batch fetch, rate-limited 0.5s/ticker |
| Deploy target | **Vite trước** → Streamlit sau | Frontend nhanh, iterate dễ |

### Tab Layout sau khi hoàn thành

```
┌─────────────┬──────────┬──────────┬──────────┬──────────┐
│ 360 Overview│   CDKT   │   KQKD   │   LCTT   │   CSTC   │
└─────────────┴──────────┴──────────┴──────────┴──────────┘
      ↑ NEW          ↑ Giữ nguyên (existing code)
```

Tab "360 Overview" bên trong chứa:
- **Company Hero** (tên, giá, vốn hóa, sector badge)
- **Snowflake Chart** (5 trục: Value, Future, Past, Health, Dividend)
- **Quick Stats** (P/E, P/B, ROE, Dividend Yield)
- **Valuation Gauge** (Undervalued ← Fair → Overvalued)
- **Checklist Cards** (pass/fail health checks)
- **Price Chart** (OHLCV area chart)

---

## 🗂️ Thư mục & File Map

### Files sẽ tạo mới (✨ NEW)

```
Finsang/
├── sub-projects/V3_SimplyWallSt/
│   ├── scripts/
│   │   ├── fetch_ohlcv_vn30.py          ← P1.1 Fetch OHLCV VN30
│   │   ├── fetch_company_overview.py     ← P1.2 Fetch market data
│   │   └── calc_snowflake.py             ← P1.4 Snowflake score calculator
│   ├── implementation_plan.md            ← This file
│   ├── findings.md
│   ├── challenges.md
│   └── logs.md
│
├── frontend/src/
│   ├── components/
│   │   ├── OverviewTab.jsx               ← P2.1 Main 360 Overview container
│   │   ├── CompanyHero.jsx               ← P2.2 Company info hero section
│   │   ├── SnowflakeChart.jsx            ← P2.3 Radar chart (Plotly)
│   │   ├── ValuationGauge.jsx            ← P2.4 P/E gauge
│   │   ├── ChecklistCards.jsx            ← P2.5 Pass/fail checks
│   │   ├── PriceChart.jsx                ← P2.6 OHLCV area chart (Plotly)
│   │   └── QuickStats.jsx                ← P2.7 Key metrics grid
│   └── hooks/
│       └── useOverviewData.js            ← P2.8 Data fetching hook
```

### Files sẽ sửa (✏️ MODIFY)

```
Finsang/
├── frontend/src/
│   ├── App.jsx                           ← P2.0 Thêm tab "360 Overview"
│   ├── App.css                           ← P3.1 Apply SWS theme
│   └── index.css                         ← P3.2 Global theme variables
│
├── sub-projects/Version_2/
│   └── metrics.py                        ← P1.5 Thêm ROE, ROA, D/E, Current Ratio
```

---

## ⚡ PHASE 1: LAYER — Backend Data Enhancement ✅ DONE

### Agent Assignment
> **Agent đã chạy**: Antigravity (conversation `0be87c46`)  
> **Skills đã dùng**: `professional-cfo-analyst`  
> **Kết quả**: 31/31 tickers VN30 fetched, upserted, scored thành công.  
> **Lưu ý cho agent mới**: KHÔNG cần chạy lại Phase 1 trừ khi cần refresh data.

---

### P1.1 — Fetch OHLCV VN30 (2025-2026) ✅ DONE

**File tạo**: `V3_SimplyWallSt/scripts/fetch_ohlcv_vn30.py`  
**File đọc trước**: `sub-projects/Version_2/sector.py` (hàm `get_all_tickers(vn30_only=True)`)  
**Ghi vào**: Supabase table `stock_ohlcv` (đã có schema)

**Logic**:
```python
# Pseudo-code
from sector import get_all_tickers
tickers = get_all_tickers(vn30_only=True)  # ~30 tickers

for ticker in tickers:
    # VNDirect/Vietcap API: 1 request = full history
    # GET https://finfo-api.vndirect.com.vn/v4/stock_prices
    #   ?sort=date&size=500&q=code:{ticker}~floor:HOSE~date:gte:2025-01-01
    data = fetch_ohlcv(ticker, start="2025-01-01", end="2026-03-01")
    upsert_to_supabase("stock_ohlcv", data)
    time.sleep(0.5)  # Rate limit
```

**API Rate Limit Strategy**:
- 30 tickers × 1 request each = 30 requests total
- Delay 0.5s between requests → ~15 seconds total
- Each response: ~365 rows (1 row per trading day)
- Total: ~10,950 rows → upsert vào `stock_ohlcv`

**Supabase table `stock_ohlcv`** (đã tồn tại, schema):  
`stock_name TEXT, time TIMESTAMPTZ, open NUMERIC, high NUMERIC, low NUMERIC, close NUMERIC, volume NUMERIC, asset_type TEXT`  
PK = `(stock_name, time)`

**Verification**: Sau khi chạy, query:
```sql
SELECT stock_name, COUNT(*) as rows 
FROM stock_ohlcv 
GROUP BY stock_name 
ORDER BY stock_name;
-- Expected: 30 tickers, mỗi ticker ~300-365 rows
```

---

### P1.2 — Fetch Company Overview (Market Data) ✅ DONE
> **Thực tế**: Dùng `vnstock` (VCI source) thay vì Vietcap API trực tiếp. Script: `V3_SimplyWallSt/scripts/fetch_company_overview.py`. 31/31 tickers upserted.

**File tạo**: `V3_SimplyWallSt/scripts/fetch_company_overview.py`  
**File đọc trước**: `sub-projects/Version_2/sector.py`  
**Ghi vào**: Supabase table `company_overview` (CẦN TẠO MỚI — xem P1.3)

**Data cần fetch per ticker**:

| Field | Source | API |
|---|---|---|
| market_cap | Vietcap hoặc TCBS | `organOverview.marketCap` |
| current_price | OHLCV latest close | `stock_ohlcv` latest row |
| pe_ratio | Vietcap | `organOverview.pe` |
| pb_ratio | Vietcap | `organOverview.pb` |
| dividend_yield | Vietcap | `organOverview.dividendYield` |
| eps_ttm | Calculated | LN ròng TTM / Shares |
| shares_outstanding | Vietcap | `organOverview.sharesOutstanding` |
| industry | Companies table | Có thể enrichment thêm |

**Primary API**: Vietcap financial overview  
**Fallback**: TCBS (đã có `get_tcbs.py` trong Version_2)

**Token Note**: Script này nhỏ (~100 lines). Agent chỉ cần đọc `sector.py` + `.env` rồi viết.

---

### P1.3 — Supabase Migration: `company_overview` table ✅ DONE
> **Migrations đã chạy**: `add_company_overview_table`, `extend_company_overview_columns`, `add_missing_overview_columns`, `allow_anon_write_company_overview`.

**Agent chạy**: Gọi MCP tool `apply_migration`  
**Đọc trước**: KHÔNG CẦN đọc file nào — chỉ chạy SQL

```sql
-- Migration: add_company_overview_table
CREATE TABLE IF NOT EXISTS company_overview (
    ticker              TEXT PRIMARY KEY REFERENCES companies(ticker),
    market_cap          NUMERIC,            -- Tỷ VND
    current_price       NUMERIC,            -- VND per share
    pe_ratio            NUMERIC,
    pb_ratio            NUMERIC,
    dividend_yield      NUMERIC,            -- %
    eps_ttm             NUMERIC,            -- VND/share
    bvps                NUMERIC,            -- Book Value Per Share
    shares_outstanding  BIGINT,
    week52_high         NUMERIC,
    week52_low          NUMERIC,
    avg_volume_30d      BIGINT,
    industry            TEXT,
    sub_industry        TEXT,
    -- Snowflake Scores (1.0 - 5.0)
    score_value         NUMERIC DEFAULT 0,
    score_future        NUMERIC DEFAULT 0,
    score_past          NUMERIC DEFAULT 0,
    score_health        NUMERIC DEFAULT 0,
    score_dividend      NUMERIC DEFAULT 0,
    score_total         NUMERIC DEFAULT 0,
    updated_at          TIMESTAMPTZ DEFAULT now()
);

-- RLS: anon = SELECT only, service_role = full access
ALTER TABLE company_overview ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_read" ON company_overview FOR SELECT USING (true);
CREATE POLICY "service_write" ON company_overview FOR ALL 
    USING (auth.role() = 'service_role');
```

---

### P1.4 — Snowflake Score Calculator ✅ DONE
> **Script**: `V3_SimplyWallSt/scripts/calc_snowflake.py`. Bank/Sec/Normal sector-aware scoring. 31/31 scores computed.

**File tạo**: `V3_SimplyWallSt/scripts/calc_snowflake.py`  
**File đọc trước**: `sub-projects/Version_2/metrics.py` (lines 415-585, hàm `calc_metrics`)  
**Skill tham chiếu**: `professional-cfo-analyst` → Step 2

**Scoring Logic** (5 dimensions, mỗi dim = 1.0 → 5.0):

```python
def calc_snowflake_scores(ticker: str) -> dict:
    """
    Returns: {score_value, score_future, score_past, 
              score_health, score_dividend, score_total}
    """
    # === VALUE (Định giá) ===
    # Input: P/E ratio from company_overview
    # P/E < 10 → 5.0, < 15 → 4.0, < 20 → 3.0, < 30 → 2.0, else → 1.0
    # Bonus: P/B < 1.5 → +0.5
    
    # === FUTURE (Tương lai) ===
    # Input: Revenue Growth YoY, EPS Growth YoY from financial_ratios (g7_1, g7_2)
    # Revenue Growth > 20% → 5.0, > 10% → 4.0, > 5% → 3.0, > 0% → 2.0, else → 1.0
    
    # === PAST (Quá khứ) ===
    # Input: ROE (calc), Net Margin trend 3Y
    # ROE > 20% → 5.0, > 15% → 4.0, > 10% → 3.0, > 5% → 2.0, else → 1.0
    
    # === HEALTH (Sức khỏe tài chính) ===
    # Input: D/E ratio, Current Ratio, Operating Cash Flow
    # D/E < 0.5 → 5.0, < 1.0 → 4.0, < 1.5 → 3.0, < 2.0 → 2.0, else → 1.0
    # + Current Ratio > 2 → +0.5, + OCF > 0 → +0.5
    
    # === DIVIDEND (Cổ tức) ===
    # Input: Dividend Yield from company_overview
    # Yield > 5% → 5.0, > 3% → 4.0, > 1% → 3.0, > 0% → 2.0, else → 1.0
    
    # === TOTAL ===
    # Sum of 5 scores / 25 * 100 = Overall %
```

**Dependencies**: Cần P1.2 + P1.3 hoàn thành trước (cần `company_overview` data).

---

### P1.5 — Extend `metrics.py`: Thêm ROE, ROA, D/E, Current Ratio ✅ DONE (via Snowflake)
> **Thực tế**: ROE/ROA/D/E được tính trực tiếp trong `calc_snowflake.py` thay vì thêm vào `metrics.py`. Không cần sửa `metrics.py`.

**File sửa**: `sub-projects/Version_2/metrics.py`  
**Đọc trước**: `metrics.py` lines 1-100 + lines 480-585 (calc_metrics routing)  
**Skill tham chiếu**: `professional-cfo-analyst`

**Cần thêm vào cuối `calc_normal_metrics()`** (trước common metrics g7):

```python
# g9 — Extended Ratios (cho Snowflake)
add_row("g9", "9) Chỉ số Sức khỏe Tài chính", "", 0, lambda p: None)

# ROE = LN ròng Cổ đông mẹ / VCSH × 100
# ROA = LN ròng / Tổng TS × 100
# D/E = Nợ phải trả / VCSH
# Current Ratio = TS ngắn hạn / Nợ ngắn hạn
# Interest Coverage = EBIT / Chi phí lãi vay
```

**Tương tự** cho `calc_bank_metrics()` và `calc_sec_metrics()`:  
- Bank: NIM, CIR (Cost-to-Income Ratio), NPL Ratio
- Securities: Operating Margin, Margin Loan / Equity

**Token optimization**: Agent chỉ đọc `metrics.py` (1 file). Thêm code vào cuối mỗi hàm calc_xxx_metrics.

---

## ⚡ PHASE 2: ASSEMBLE — Frontend Components ✅ DONE

### Agent Assignment
> **Agent đã chạy**: Antigravity  
> **Kết quả**: Toàn bộ components đã tạo, hoạt động trên `http://localhost:5173`.  
> **Quyết định thay đổi**: Dùng **Pure SVG** cho tất cả charts thay vì Plotly.js → giảm bundle 100%.

---

### P2.0 — Thêm Tab "360 Overview" vào App.jsx

**File sửa**: `frontend/src/App.jsx`  
**Đọc trước**: `App.jsx` (lines 25-30 → REPORT_TABS constant, lines 290-320 → tabs render)

**Thay đổi duy nhất**: Thêm 1 entry vào `REPORT_TABS`:
```javascript
const REPORT_TABS = [
  { id: '360', label: '360 Overview', table: null },  // ← NEW: No Supabase table, custom component
  { id: 'CDKT', label: 'Cân đối kế toán', table: 'balance_sheet_wide' },
  { id: 'KQKD', label: 'Kết quả kinh doanh', table: 'income_statement_wide' },
  { id: 'LCTT', label: 'Lưu chuyển tiền tệ', table: 'cash_flow_wide' },
  { id: 'CSTC', label: 'Chỉ số tài chính', table: 'financial_ratios_wide' },
]
```

**Trong render section**, thêm conditional:
```jsx
{reportType === '360' ? (
  <OverviewTab ticker={ticker} sector={sector} />
) : (
  /* existing table rendering code — GIỮ NGUYÊN */
)}
```

**Token note**: Sửa ~20 lines trong App.jsx. Không cần đọc toàn bộ.

---

### P2.1 — OverviewTab.jsx (Container Component)

**File tạo**: `frontend/src/components/OverviewTab.jsx`  
**Đọc trước**: KHÔNG CẦN (pure new file)

```jsx
// Layout structure:
// ┌──────────────────────────────────────────────┐
// │ CompanyHero (name, price, market cap, sector) │
// ├────────────────────┬─────────────────────────┤
// │  SnowflakeChart    │    QuickStats Grid      │
// │  (5-axis radar)    │    (P/E, P/B, ROE...)   │
// ├────────────────────┴─────────────────────────┤
// │  ValuationGauge (full width)                  │
// ├──────────────────────────────────────────────┤
// │  ChecklistCards (pass/fail grid)              │
// ├──────────────────────────────────────────────┤
// │  PriceChart (OHLCV area chart)                │
// └──────────────────────────────────────────────┘

import { useOverviewData } from '../hooks/useOverviewData'
// Props: { ticker, sector }
// Calls useOverviewData(ticker) → returns { overview, ohlcv, loading }
```

---

### P2.2 — CompanyHero.jsx

**Props**: `{ companyName, ticker, exchange, sector, currentPrice, marketCap, priceChange }`

```
┌─────────────────────────────────────────────┐
│ 🏢 CTCP Thủy sản Vĩnh Hoàn              │
│ VHC:HOSE                    Phi tài chính  │
│                                              │
│ ₫ 82,500    ▲ +1,200 (+1.47%)              │
│ Vốn hóa: 14,850 Tỷ VND                     │
└─────────────────────────────────────────────┘
```

**Data source**: `company_overview` table via `useOverviewData` hook.

---

### P2.3 — SnowflakeChart.jsx (Plotly Radar)

**Props**: `{ scores: { value, future, past, health, dividend } }`

**Plotly trace**:
```javascript
const data = [{
  type: 'scatterpolar',
  r: [scores.value, scores.future, scores.past, scores.health, scores.dividend],
  theta: ['Định giá', 'Tương lai', 'Quá khứ', 'Sức khỏe TC', 'Cổ tức'],
  fill: 'toself',
  fillcolor: 'rgba(38, 174, 80, 0.15)',
  line: { color: '#26AE50', width: 2 }
}]

const layout = {
  polar: {
    bgcolor: '#1A1A1A',
    radialaxis: { range: [0, 5], showticklabels: false },
    angularaxis: { color: '#A0AEC0' }
  },
  paper_bgcolor: '#1A1A1A',
  font: { color: '#FFFFFF' },
  showlegend: false,
  margin: { t: 30, b: 30, l: 50, r: 50 }
}
```

**Streamlit equivalent** (cho migration sau):
```python
import plotly.graph_objects as go
fig = go.Figure(go.Scatterpolar(
    r=[3.5, 4.0, 2.5, 4.5, 1.0],
    theta=['Định giá','Tương lai','Quá khứ','Sức khỏe TC','Cổ tức'],
    fill='toself'
))
st.plotly_chart(fig)
```

---

### P2.4 — ValuationGauge.jsx

**Props**: `{ peRatio, industryAvgPE }`

**Logic**: 
- `discount = (1 - peRatio / industryAvgPE) * 100`
- Hiển thị gauge ngang: Green (< -20%) → Yellow (-20% to 20%) → Red (> 20%)
- Dùng Plotly `indicator` type hoặc CSS animation.

**Plotly approach**:
```javascript
const data = [{
  type: 'indicator',
  mode: 'gauge+number',
  value: peRatio,
  gauge: {
    axis: { range: [0, 40] },
    bar: { color: peRatio < 15 ? '#26AE50' : peRatio < 25 ? '#F59E0B' : '#E53935' },
    steps: [
      { range: [0, 15], color: 'rgba(38,174,80,0.1)' },
      { range: [15, 25], color: 'rgba(245,158,11,0.1)' },
      { range: [25, 40], color: 'rgba(229,57,53,0.1)' }
    ]
  }
}]
```

---

### P2.5 — ChecklistCards.jsx

**Props**: `{ checks: [{ label, passed, detail }] }`

**Checklist items** (tùy theo sector):

| # | Check (Normal) | Pass Condition | Data Field |
|---|---|---|---|
| 1 | P/E thấp hơn trung bình ngành | P/E < Industry P/E | `company_overview.pe_ratio` |
| 2 | Lãi ròng tăng trưởng | EPS Growth > 0% | `financial_ratios` g7_2 |
| 3 | Nợ có thể quản lý | D/E < 1.0 | Calculated |
| 4 | Dòng tiền dương | Operating CF > 0 | `cash_flow` lctt_kd |
| 5 | Cổ tức ổn định | Div Yield > 0% | `company_overview.dividend_yield` |
| 6 | ROE trên trung bình | ROE > 15% | Calculated |

**UI**: 
```
✅ P/E thấp hơn trung bình ngành (15.2x vs 18.5x)
✅ Lãi ròng tăng trưởng (+12.3% YoY)
❌ Nợ cao hơn mức an toàn (D/E = 1.35)
✅ Dòng tiền hoạt động dương (3,450 Tỷ VND)  
```

**Styling**: Dùng `.checklist-card` từ `design-themes/simply-wall-st-theme/theme.css`

---

### P2.6 — PriceChart.jsx (OHLCV Area Chart)

**Props**: `{ ticker }`  
**Data source**: `stock_ohlcv` table → fetch 365 rows latest

**Plotly trace**:
```javascript
const data = [{
  type: 'scatter',
  mode: 'lines',
  x: dates,          // ['2025-01-02', '2025-01-03', ...]
  y: closePrices,    // [82000, 83500, ...]
  fill: 'tozeroy',
  fillcolor: 'rgba(38, 174, 80, 0.08)',
  line: { color: '#26AE50', width: 1.5 }
}]
```

---

### P2.7 — QuickStats.jsx

**Props**: `{ stats: { pe, pb, roe, divYield, marketCap, eps } }`

```
┌──────────┬──────────┬──────────┬──────────┐
│  P/E     │  P/B     │  ROE     │ Div Yield│
│  15.2x   │  2.3x    │  18.5%   │  3.2%    │
├──────────┼──────────┼──────────┼──────────┤
│ Vốn hóa  │  EPS     │ 52W High │ 52W Low  │
│ 14,850T  │  5,430đ  │ 95,000đ  │ 62,000đ  │
└──────────┴──────────┴──────────┴──────────┘
```

---

### P2.8 — useOverviewData.js (Custom Hook)

**File tạo**: `frontend/src/hooks/useOverviewData.js`

```javascript
export function useOverviewData(ticker) {
  // 1. Fetch company_overview (single row)
  //    supabase.from('company_overview').select('*').eq('ticker', ticker).single()
  
  // 2. Fetch OHLCV (latest 365 rows)
  //    supabase.from('stock_ohlcv').select('*')
  //      .eq('stock_name', ticker)
  //      .gte('time', '2025-01-01')
  //      .order('time', { ascending: true })
  
  // Returns: { overview, ohlcv, loading, error }
}
```

---

## ⚡ PHASE 3: STYLE — SWS Theme Integration ✅ DONE

### Agent Assignment
> **Agent đã chạy**: Antigravity  
> **Kết quả**: 420+ lines CSS appended vào `App.css`. Dark theme OLED, Inter font, hover animations.

---

### P3.1 — Apply SWS CSS Variables

**File sửa**: `frontend/src/index.css`  
**Đọc trước**: `design-themes/simply-wall-st-theme/theme.css` (toàn bộ 49 lines)

Merge SWS CSS variables vào `:root`:
- `--s-bg-main: #1A1A1A`  
- `--s-bg-sidebar: #262626`  
- `--s-text-primary: #FFFFFF`  
- `--s-success: #26AE50`  
- `--s-danger: #E53935`  
- Font: `"Inter", -apple-system, sans-serif`

### P3.2 — 360 Overview Tab Styling

**File sửa**: `frontend/src/App.css`

Thêm styles cho:
- `.overview-tab` — grid layout cho 360 tab
- `.company-hero` — gradient background, large text
- `.quick-stats-grid` — 2×4 metric cards
- `.checklist-card` — copy từ theme.css (border, hover, transition)
- `.snowflake-container` — centered within grid
- Animations: fade-in khi chuyển tab, hover scale trên cards

### P3.3 — Typography Enhancement

Import Google Font "Inter" via CDN trong `index.html`:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

---

## ⚡ PHASE 4: TEST — Verification & Audit ✅ DONE

### Agent Assignment
> **Agent đã chạy**: Antigravity  
> **Kết quả**: Browser test passed (VHC, VCB, SSI). CTO/CFO audit documented in `v3_walkthrough.md`.  
> **Xem thêm**: `v3_walkthrough.md` (artifact) cho báo cáo audit hoàn chỉnh.

---

### P4.1 — Data Verification

```sql
-- Verify stock_ohlcv has VN30 data
SELECT stock_name, MIN(time), MAX(time), COUNT(*)
FROM stock_ohlcv 
GROUP BY stock_name ORDER BY stock_name;
-- Expected: 30 tickers, dates from 2025 to 2026

-- Verify company_overview populated
SELECT ticker, pe_ratio, pb_ratio, score_total
FROM company_overview ORDER BY ticker;
-- Expected: 30+ rows with non-null values
```

### P4.2 — Browser Test Checklist

| # | Test | Action | Expected |
|---|---|---|---|
| 1 | Load page | Navigate to localhost:5173 | Header renders, default ticker loaded |
| 2 | Tab "360 Overview" | Click "360 Overview" tab | Snowflake + Hero + QuickStats render |
| 3 | Normal ticker | Select VHC | All 5 tabs work, 360 shows full data |
| 4 | Bank ticker | Select VCB | Sector badge = "Ngân hàng", 360 adjusts |
| 5 | Securities ticker | Select SSI | Sector badge = "Chứng khoán", 360 adjusts |
| 6 | Data integrity | Check P/E value | Matches Vietcap website ±5% |
| 7 | OHLCV chart | View price chart | Shows 2025-2026 price line |
| 8 | Checklist | View checklist cards | Pass/fail icons with explanations |
| 9 | Existing tabs | Click CDKT tab | Data table renders correctly (no regression) |
| 10 | Theme | Visual inspection | Dark background #1A1A1A, Inter font |

### P4.3 — CTO Audit Checklist ✅

- [x] RLS enabled on `company_overview` table
- [x] No exposed API keys in frontend source
- [x] Error handling in `useOverviewData` hook
- [x] Loading states for all async data
- [x] No N+1 query patterns (3 parallel queries in hook)
- [x] Bundle size: 0KB chart deps (Pure SVG, Plotly removed)

### P4.4 — CFO Validation ✅

- [x] P/E = Current Price / EPS → VHC 10.1x verified
- [x] ROE = Net Income / Equity → VHC 15.0% verified
- [x] Snowflake scores sensible (VHC: Value=3.5, Health=3.1, Dividend=3.0)
- [x] No pie charts used anywhere (IBCS compliance)
- [x] Balance Sheet equation holds (verified in existing V2 audit)

---

## 📊 Execution Roadmap

### Phase Dependencies & Parallelism

```
P1.1 (OHLCV VN30) ─────────────┐
                                 ├──→ P1.4 (Snowflake calc) ──→ P2.3 (SnowflakeChart)
P1.2 (Company overview fetch) ──┤                              P2.4 (ValuationGauge)
                                 │                              P2.5 (Checklists)
P1.3 (Migration SQL) ──────────┘
                                                                
P1.5 (metrics.py extend) ─ INDEPENDENT ─────────────────────→ P2.7 (QuickStats)

P2.0 (App.jsx tab add) ────────→ P2.1 (OverviewTab) ────────→ P3.x (Styling)
P2.8 (useOverviewData hook) ───→ P2.2-P2.6 (Components)      → P4.x (Testing)
P2.6 (PriceChart) ← needs P1.1
```

### Recommended Agent Session Plan

| Session | Phase | Agent Type | Est. Tokens | Files Touched |
|---|---|---|---|---|
| **S1** | P1.3 | Any | ~2K | SQL migration only |
| **S2** | P1.1 | Data | ~8K | `fetch_ohlcv_vn30.py`, `sector.py` |
| **S3** | P1.2 | Data | ~6K | `fetch_company_overview.py` |
| **S4** | P1.4 | Data/CFO | ~6K | `calc_snowflake.py`, `metrics.py` (read only) |
| **S5** | P1.5 | Backend | ~5K | `metrics.py` |
| **S6** | P2.0 + P2.8 | Frontend | ~8K | `App.jsx`, `useOverviewData.js` |
| **S7** | P2.1-P2.3 | Frontend | ~10K | `OverviewTab`, `CompanyHero`, `SnowflakeChart` |
| **S8** | P2.4-P2.7 | Frontend | ~10K | `ValuationGauge`, `Checklists`, `PriceChart`, `QuickStats` |
| **S9** | P3.1-P3.3 | UI | ~5K | `index.css`, `App.css`, `index.html` |
| **S10** | P4.1-P4.4 | CTO/CFO | ~6K | SQL queries + browser tests |

**Total estimated**: ~66K tokens across 10 sessions

### Optimal Parallel Execution

```
Timeline:   ─────────────────────────────────────────────>

Session 1:  [S1: Migration]
Session 2:  [S2: OHLCV fetch]  +  [S5: metrics.py]  ← PARALLEL
Session 3:  [S3: Overview fetch]
Session 4:  [S4: Snowflake calc]
Session 5:  [S6: App.jsx + Hook]
Session 6:  [S7: Core components]  +  [S9: CSS theme]  ← PARALLEL
Session 7:  [S8: Remaining components]
Session 8:  [S10: Testing & Audit]
```

→ **8 sequential sessions** (khi tối ưu parallel) vs 10 sessions nếu chạy tuần tự.

---

## 📦 NPM Dependencies (Phase 2)

```bash
cd frontend
npm install plotly.js-dist-min react-plotly.js
# plotly.js-dist-min: ~1MB (lighter than full plotly.js ~3.5MB)
# react-plotly.js: React wrapper for Plotly
```

**Bundle impact**: +~200KB gzipped (chấp nhận cho dashboard app).

---

## 🔗 Quick Reference for Agents

### Supabase Connection
```
Project ID: zuphshdgudnwlfjlfbbs
Region: ap-southeast-1
DB Host: db.zuphshdgudnwlfjlfbbs.supabase.co
```
Environment variables in `Finsang/.env`:
- `SUPABASE_URL`
- `SUPABASE_KEY` (service role for backend)
- Frontend uses `frontend/.env` (anon key)

### Key Existing Functions (DO NOT REWRITE)
- `sector.py → get_sector(ticker)` — Returns 'bank' | 'sec' | 'normal'
- `sector.py → get_all_tickers(vn30_only=True)` — Returns 30 VN30 tickers
- `pipeline.py → load_tab_from_supabase()` — Loads financial data
- `metrics.py → calc_metrics(ticker, period)` — Calculates all ratios
- `supabaseClient.js` — Frontend Supabase client (already configured)

### VN Market Specific Notes
- Đơn vị giá: VND (không phải USD)
- Format: `82,500 ₫` hoặc `82.5K`
- Quý: `Q1/2025`, `Q2/2025` (không phải Q1 2025)
- Năm tài chính: trùng năm dương lịch (1/1 → 31/12)
- Sàn: HOSE, HNX, UPCOM
- Industry P/E benchmark: Dùng VN30 average nếu chưa có industry data

---
---

# 🔮 V3.1 Enhancement Plan — Simply Wall St Feature Parity

> **Date**: 2026-03-01 | **Status**: 📋 Planning
> **Reference**: [MBB Financial Health on SWS](https://simplywall.st/stocks/vn/banks/hose-mbb/military-commercial-bank-shares/health)
> **Goal**: Nâng cấp 360 Overview từ "báo cáo tóm tắt 1 tab" thành hệ thống multi-section chuyên sâu giống SWS.

---

## 📊 Gap Analysis: Finsang V3.0 vs. Simply Wall St

### Tính năng SWS có mà Finsang V3.0 CHƯA CÓ

| # | Tính năng SWS | Finsang hiện tại | Ưu tiên | Độ khó |
|---|---|---|---|---|
| G-01 | **7 sidebar tabs** (Overview, Valuation, Future, Past, Health, Dividend, Management) | Chỉ có 1 tab "360 Overview" duy nhất | 🔴 HIGH | Medium |
| G-02 | **Financial Health page riêng biệt** với bank-specific checks (Asset/Equity, NIM, Bad Loans, Loan/Deposit) | Checklists nằm chung trong Overview, thiếu bank metrics chuyên sâu | 🔴 HIGH | Medium |
| G-03 | **Financial Position Analysis** (Stacked Bar: Assets vs Liabilities, Short-Term vs Long-Term) | Chưa có | 🟡 MED | Medium |
| G-04 | **Debt to Equity History chart** (line+area trend 5-10 năm) | Chưa có | 🟡 MED | Low |
| G-05 | **Checklist expandable cards** với narrative giải thích chi tiết | Chỉ có flat pass/fail, chưa có detail card mở rộng | 🟡 MED | Low |
| G-06 | **"Key Information" summary box** (Asset/Equity ratio, NIM, Total deposits, Loan/Deposit, Bad loans, Allowance) | QuickStats chỉ show P/E, P/B, ROE, Dividend — thiếu bank-specific | 🔴 HIGH | Low |
| G-07 | **"Recent financial health updates"** (news/alert feed) | Chưa có | 🟢 LOW | High |
| G-08 | **Sidebar navigation** sticky bên trái (SWS style) | Tab ngang trên cùng — không giống SWS | 🟢 LOW | Medium |

### Tính năng Finsang đã có nhưng CẦN CẢI TIẾN

| # | Tính năng | Hiện tại | Cần cải tiến |
|---|---|---|---|
| I-01 | Checklist scoring | `4/6 đạt` — chỉ show tổng | Thêm icon row (✅❌✅✅✅❌) giống SWS header |
| I-02 | QuickStats grid | P/E, P/B, ROE, Div — 2×4 grid | Bank-aware: thay ROE bằng NIM cho bank, D/E bằng Asset/Equity |
| I-03 | Snowflake Chart | 5 trục giá trị đúng | Cần animation smooth khi switch ticker |
| I-04 | ValuationGauge | CSS gradient đơn giản | Thêm label text "Undervalued" / "Fair Value" / "Overvalued" |

---

## 🏗️ V3.1 Phase Architecture

### Phase 5: Financial Health Deep-Dive (PRIORITY 1)

> **Agent**: Frontend + Data Agent
> **Skills**: `professional-cfo-analyst`, `kpi-dashboard-design`
> **Token ước tính**: ~15K tokens (3 sessions)

#### P5.1 — Bank-Specific Key Information Box

**Component mới**: `BankKeyInfo.jsx`
**Props**: `{ overview, sector }`

Hiển thị khác nhau theo sector:

```
=== BANK (sector='bank') ===
┌──────────────────────────────────────────────────┐
│ Key Information                                   │
│                                                   │
│ ┌─────────────────┬──────────────────┐           │
│ │ 11.4x           │ NIM: 3.8%        │           │
│ │ Asset to Equity  │ Net Interest     │           │
│ └─────────────────┴──────────────────┘           │
│                                                   │
│ Total deposits        đ1,152.48t                  │
│ Loan to deposit ratio    Appropriate              │
│ Bad loans                1.3%                     │
│ Allowance for bad loans  Low                      │
│ Cash & equivalents       đ177.70t                 │
└──────────────────────────────────────────────────┘

=== NON-FINANCIAL (sector='normal') ===
┌──────────────────────────────────────────────────┐
│ Key Information                                   │
│ ┌─────────────────┬──────────────────┐           │
│ │ D/E: 0.85       │ Current: 1.4      │           │
│ │ Debt to Equity   │ Current Ratio     │           │
│ └─────────────────┴──────────────────┘           │
│                                                   │
│ Total Debt             đ5,230t                    │
│ Total Equity           đ6,150t                    │
│ Net Cash / Net Debt    Net Cash                   │
│ Interest Coverage      8.5x                       │
│ Cash & equivalents     đ1,200t                    │
└──────────────────────────────────────────────────┘
```

**Data Sources** (vnstock `company.ratio_summary()`):
- Bank: `asset_to_equity` (tự tính = Total Assets / Equity), `nim` (net interest margin), `loan_to_deposit`, `bad_loans_pct`, `allowance_bad_loans`
- Normal: `de_ratio`, `current_ratio`, `interest_coverage`, `cash_and_equivalents`

---

#### P5.2 — Financial Position Stacked Bar Chart (Balance Sheet Visual)

**Component mới**: `FinancialPositionChart.jsx`
**Render**: Pure SVG stacked bars

```
         Assets                    Liabilities + Equity
    ┌──────────────┐         ┌──────────────────────────┐
    │              │         │ Liabilities               │
    │  Assets      │         │ (Deposits / Debts)        │
    │  (cyan)      │         │ (light blue)              │
    │              │         ├──────────────────────────┤
    │              │         │ Equity                    │
    │              │         │ (green)                   │
    └──────────────┘         └──────────────────────────┘
     Short Term                Long Term
```

**Data**: `balance_sheet_wide` table → Extract:
- Short-term assets, long-term assets
- Short-term liabilities, long-term liabilities
- Total equity

---

#### P5.3 — Debt-to-Equity History Trend Chart

**Component mới**: `DebtEquityHistoryChart.jsx`
**Render**: Pure SVG area + line chart (giống PriceChart pattern)

```
         Debt-to-Equity History
    đ260t ┌────────────────────────────────┐
          │               ╱ Debt (red)     │
    đ130t │         ╱────╱                 │
          │   ╱────╱                       │
        0 │──╱───────── Equity (blue) ─────│
          └────────────────────────────────┘
           2020   2021   2022   2023   2024
```

**Data**: `balance_sheet_wide` → historical periods → extract "Nợ phải trả" + "VCSH"

---

#### P5.4 — Expandable Checklist Cards

**Cải tiến**: `ChecklistCards.jsx`
Thêm khả năng mở rộng (expand/collapse) cho mỗi check item:

```
✅ P/E thấp hơn trung bình ngành ──── [▼ Xem chi tiết]
   │
   └── P/E của VHC là 10.1x, thấp hơn mức trung bình ngành
       Phi tài chính VN30 (16x). Điều này cho thấy cổ phiếu
       đang được định giá hấp dẫn so với peers.
```

**Logic**: Giữ nguyên `buildChecks()`, thêm field `narrative` cho mỗi check.
**CSS**: Thêm `.check-item.expanded` với `max-height` transition.

---

### Phase 6: Multi-Section 360 Tab Layout (PRIORITY 2)

> **Agent**: Frontend Agent
> **Skills**: `ui-ux-pro-max`, `frontend-design`
> **Token ước tính**: ~10K tokens (2 sessions)

#### P6.1 — Section-Based Navigation trong 360 Tab

Thay vì tạo 7 tabs mới riêng biệt (quá rộng cho phase này), chia 360 Overview thành **sections có anchor navigation**:

```
┌──────────────────────────────────────────────────────────┐
│ 🔭 360 Overview                                          │
│                                                          │
│ [Summary] [Valuation] [Health] [History] [Dividend]      │   ← internal anchors
│                                                          │
│ ═══ Summary ═══                                          │
│ CompanyHero + SnowflakeChart + QuickStats                │
│                                                          │
│ ═══ Valuation ═══                                        │
│ ValuationGauge + PeerComparison                          │
│                                                          │
│ ═══ Financial Health ═══                                 │
│ BankKeyInfo + FinancialPositionChart + ChecklistCards     │
│                                                          │
│ ═══ History ═══                                          │
│ DebtEquityHistoryChart + PriceChart                      │
│                                                          │
│ ═══ Dividend ═══                                         │
│ DividendYieldCard + DividendHistoryChart                  │
└──────────────────────────────────────────────────────────┘
```

**Implementation**: Scroll-based with `scrollIntoView({ behavior: 'smooth' })`.
**CSS**: `.section-nav` sticky bar xám nhạt chứa anchor links.

---

#### P6.2 — Checklist Header Icon Row

Giống SWS: trên cùng trang Health section hiển thị tổng quan:

```
Financial Health criteria checks 5/6  ✅ ❌ ✅ ✅ ✅ ✅   [→]
```

**Component**: Mở rộng `ChecklistCards.jsx` → thêm icon-only summary row.

---

### Phase 7: Data Pipeline Enhancement (PRIORITY 3)

> **Agent**: Data Engineer Agent
> **Skills**: `data-engineering-data-pipeline`, `professional-cfo-analyst`
> **Token ước tính**: ~8K tokens (2 sessions)

#### P7.1 — Fetch Bank-Specific Metrics

**Script mới hoặc mở rộng**: `fetch_company_overview.py`

Thêm fields cho bank tickers:
```python
# Từ vnstock company.ratio_summary() hoặc company.overview()
BANK_EXTRA_FIELDS = {
    'nim':                    'net_interest_margin',
    'loan_to_deposit':        'loan_to_deposit_ratio',
    'bad_loans_pct':          'npl_ratio',       # Non-performing loan %
    'allowance_bad_loans':    'provision_coverage_ratio',
    'total_deposits':         'total_deposits',
    'total_loans':            'total_loans',
    'asset_to_equity':        'financial_leverage',  # Total Assets / Equity
}
```

**Migration**: Thêm columns vào `company_overview`:
```sql
ALTER TABLE company_overview
  ADD COLUMN IF NOT EXISTS nim                DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS npl_ratio          DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS provision_coverage DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS loan_to_deposit    DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS total_deposits     DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS total_loans        DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS financial_leverage DOUBLE PRECISION;
```

#### P7.2 — Historical Balance Sheet Summary Cache

Tạo view hoặc table riêng tóm tắt historical D/E + Assets/Liabilities:

```sql
-- View cho D/E History chart
CREATE OR REPLACE VIEW balance_sheet_summary AS
SELECT
    stock_name,
    (periods_data)::jsonb as year_values,
    item_id
FROM balance_sheet_wide
WHERE item_id IN ('cdkt_npt', 'cdkt_vcsh', 'cdkt_tts', 'cdkt_tsnh', 'cdkt_tsdh', 'cdkt_nnh', 'cdkt_ndh')
ORDER BY stock_name, item_id;
```

---

## 📋 V3.1 Execution Roadmap

```
Phase 5 (Health Deep-Dive)   ░░░░░░░░░░░░  ~45% effort
Phase 6 (Multi-Section Nav)  ░░░░░░░░░░░░  ~30% effort
Phase 7 (Data Pipeline)      ░░░░░░░░░░░░  ~25% effort
```

### Session Plan

| Session | Phase | Nội dung | Est. Tokens |
|---|---|---|---|
| S11 | P7.1 | Fetch bank metrics + DB migration | ~5K |
| S12 | P5.1 + P5.2 | BankKeyInfo + FinancialPositionChart | ~8K |
| S13 | P5.3 + P5.4 | DebtEquityHistoryChart + Expandable Checklists | ~7K |
| S14 | P6.1 + P6.2 | Section navigation + Checklist header icons | ~8K |
| S15 | P7.2 + Test	| Historical BS view + Browser tests | ~5K |

### Dependency Chain

```
P7.1 (bank data) ─────→ P5.1 (BankKeyInfo)
                          │
P7.2 (BS summary) ────→ P5.2 (FinancialPositionChart)
                          │
                          ├──→ P5.3 (D/E History)
                          │
P5.4 (Expandable) ─────→ P6.1 (Section nav) ──→ P6.2 (Icon row)
```

> **CRITICAL**: P7.1 phải hoàn thành TRƯỚC P5.1 (bank metrics cần data).
> P5.2 và P5.3 có thể chạy SONG SONG vì dùng data khác nhau từ `balance_sheet_wide`.
> P6.x chạy SAU khi tất cả P5.x components đã xong.
