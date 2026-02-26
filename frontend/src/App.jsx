import { useEffect, useState, useMemo } from 'react'
import { supabase } from './supabaseClient'
import './App.css'

// ─── V2 Data Source ────────────────────────────────────────────────────────
// Data synced from Version 2 Parquet pipeline (Vietcap API → Parquet → Supabase).
// Wide views pivot rows via jsonb_object_agg(period, value) = periods_data JSONB.
// Values stored in Tỷ VND. Display in Triệu VND (×1000).
// ────────────────────────────────────────────────────────────────────────────

const TICKERS = [
  { code: 'VHC', name: 'CTCP Vĩnh Hoàn', exchange: 'HOSE' },
  { code: 'FPT', name: 'CTCP Tập đoàn FPT', exchange: 'HOSE' },
  { code: 'HPG', name: 'CTCP Tập đoàn Hoà Phát', exchange: 'HOSE' },
]

const REPORT_TABS = [
  { id: 'CDKT', label: 'Cân đối kế toán', table: 'balance_sheet_wide' },
  { id: 'KQKD', label: 'Kết quả kinh doanh', table: 'income_statement_wide' },
  { id: 'LCTT', label: 'Lưu chuyển tiền tệ', table: 'cash_flow_wide' },
  { id: 'CSTC', label: 'Chỉ số tài chính', table: 'financial_ratios_wide' },
]

const PERIOD_FILTERS = [
  { id: 'year', label: 'Năm' },
  { id: 'quarter', label: 'Quý' },
]

// ─── Helpers ──────────────────────────────────────────────────────────────

// Format: Raw VND (đồng) → Tỷ VND (÷ 1,000,000,000)
function formatNumber(num) {
  if (num === null || num === undefined) return ''
  if (typeof num !== 'number') return '' // Handle entirely empty cells
  if (num === 0) return '–'
  const inBillions = num / 1000000000
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  }).format(inBillions)
}

// Format period for header: "Q4/2024" or "2024" displayed as-is
function formatPeriodLabel(p) {
  if (!p) return p
  return p
}

// Is this a major heading row (bold, uppercase)?
function isMajorHeading(row) {
  return (
    row.levels === 0 ||
    row.item?.startsWith('TỔNG') ||
    row.item?.startsWith('Cộng') ||
    /^[IVX]+\./.test(row.item || '')
  )
}

// ─── App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [ticker, setTicker] = useState('VHC')
  const [reportType, setReportType] = useState('CDKT')
  const [periodFilter, setPeriodFilter] = useState('year')
  const [periods, setPeriods] = useState([])
  const [expandedRows, setExpandedRows] = useState({})

  const currentTicker = TICKERS.find(t => t.code === ticker) || TICKERS[0]
  const currentTab = REPORT_TABS.find(t => t.id === reportType) || REPORT_TABS[0]

  useEffect(() => {
    async function fetchData() {
      setLoading(true)

      const { data: reports, error } = await supabase
        .from(currentTab.table)
        .select('*')
        .eq('stock_name', ticker)
        .order('row_number', { ascending: true })

      if (error) {
        console.error('Supabase error:', error)
        setData([]); setPeriods([]); setLoading(false); return
      }
      if (!reports || reports.length === 0) {
        setData([]); setPeriods([]); setLoading(false); return
      }

      // Build parent tree and fallback heuristic if levels are missing
      let seenL1 = new Set();
      const needsHeuristic = reports.every(r => r.levels === 0 || r.levels == null);

      const processedLevels = reports.map((row) => {
        let level = row.levels || 0;
        if (needsHeuristic) {
          const str = (row.item || '').trim();
          const lower = str.toLowerCase();
          if (str === str.toUpperCase() && /[A-ZÀ-Ỹ]/.test(str)) {
            level = 0;
          } else if (currentTab.id === 'CDKT') {
            const l1_keywords = [
              'tiền và tương đương tiền', 'đầu tư ngắn hạn', 'đầu tư tài chính ngắn hạn',
              'các khoản phải thu ngắn hạn', 'các khoản phải thu', 'hàng tồn kho',
              'tài sản ngắn hạn khác', 'tài sản lưu động khác', 'các khoản phải thu dài hạn',
              'phải thu dài hạn', 'tài sản cố định', 'bất động sản đầu tư', 'tài sản dở dang dài hạn',
              'đầu tư dài hạn', 'đầu tư tài chính dài hạn', 'tài sản dài hạn khác',
              'nợ ngắn hạn', 'nợ dài hạn', 'vốn chủ sở hữu', 'nguồn kinh phí'
            ];
            // Assign L1 only on first occurrence to allow L2s with same name (e.g. "Hàng tồn kho")
            if (l1_keywords.some(kw => lower === kw) && !seenL1.has(lower)) {
              level = 1;
              seenL1.add(lower);
            } else {
              level = 2;
            }
          } else {
            // For non-balance sheet tabs, default everything that isn't L0 to L1
            level = 1;
          }
        }
        return { ...row, computed_level: level };
      });

      const processed = processedLevels.map((row, i) => {
        let parent_id = null;
        if (row.computed_level > 0) {
          for (let j = i - 1; j >= 0; j--) {
            if (processedLevels[j].computed_level === row.computed_level - 1) {
              parent_id = processedLevels[j].item_id;
              break;
            }
          }
        }
        return { ...row, parent_id, levels: row.computed_level }
      })

      setData(processed)

      // Collect period columns from periods_data, filter by year/quarter
      const allPeriods = new Set()
      processed.forEach(r => {
        Object.keys(r.periods_data || {}).forEach(p => allPeriods.add(p))
      })

      let filteredPeriods = Array.from(allPeriods)
      if (periodFilter === 'year') {
        filteredPeriods = filteredPeriods.filter(p => /^\d{4}$/.test(p))
        // Sort years: 2025, 2024, 2023...
        filteredPeriods.sort((a, b) => b.localeCompare(a))
      } else {
        filteredPeriods = filteredPeriods.filter(p => /^Q\d\/\d{4}$/.test(p))
        // Sort quarters chronologically descending: Q4/2025, Q3/2025, Q2/2025...
        filteredPeriods.sort((a, b) => {
          // p is like "Q1/2025"
          const [, qA, yA] = a.match(/Q(\d)\/(\d{4})/) || []
          const [, qB, yB] = b.match(/Q(\d)\/(\d{4})/) || []
          if (!yA || !yB) return b.localeCompare(a)
          if (yA !== yB) return parseInt(yB) - parseInt(yA) // Year desc
          return parseInt(qB) - parseInt(qA) // Quarter desc within same year
        })
      }

      // Take latest 8 periods
      const cols = filteredPeriods.slice(0, 8)
      setPeriods(cols)

      // Auto-expand L0 + L1
      const defaultExpanded = {}
      processed.forEach(r => { if (r.levels <= 1) defaultExpanded[r.item_id] = true })
      setExpandedRows(defaultExpanded)
      setLoading(false)
    }
    fetchData()
  }, [ticker, reportType, periodFilter])

  const dataMap = useMemo(() => {
    const m = {}; data.forEach(r => { m[r.item_id] = r }); return m
  }, [data])

  const isVisible = (row) => {
    if (row.levels === 0) return true
    let curr = dataMap[row.parent_id]
    while (curr) {
      if (!expandedRows[curr.item_id]) return false
      curr = dataMap[curr.parent_id]
    }
    return true
  }

  const toggle = (id) => setExpandedRows(p => ({ ...p, [id]: !p[id] }))

  // ── Mini Bar Chart ─────────────────────────────────────────────────────
  const MiniBarChart = ({ values }) => {
    if (!values || values.length === 0) return <span className="no-chart">–</span>
    const maxVal = Math.max(...values.map(Math.abs)) || 1
    const hasNeg = values.some(v => v < 0)
    return (
      <div className={`mini-bar-container${hasNeg ? ' mixed' : ''}`}>
        {values.map((v, i) => {
          const scale = Math.min(1, Math.max(0.04, Math.abs(v) / maxVal))
          return (
            <div key={i} className="bar-col" title={formatNumber(v)}>
              <div className="bar-pos-area">
                {v >= 0 && <div className="bar-fill pos" style={{ transform: `scaleY(${scale})` }} />}
              </div>
              <div className="bar-neg-area">
                {v < 0 && <div className="bar-fill neg" style={{ transform: `scaleY(${scale})` }} />}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  // ── Stat summary cards ─────────────────────────────────────────────────
  const statSummary = useMemo(() => {
    if (!data.length || !periods.length) return null
    const latestPeriod = periods[0]
    const rowCount = data.length
    const filledCount = data.filter(r => r.periods_data?.[latestPeriod] != null).length
    const coverage = rowCount > 0 ? Math.round((filledCount / rowCount) * 100) : 0
    return { latestPeriod, rowCount, filledCount, coverage }
  }, [data, periods])

  return (
    <div className="app">
      {/* ═══ Header ═══ */}
      <header className="app-header">
        <div className="brand">
          <svg className="brand-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          <span className="brand-name">Finsang Terminal</span>
          <span className="brand-version">v2.0</span>
        </div>
        <div className="header-right">
          <span className="data-source">Vietcap Data</span>
          <span className="ticker-badge">{ticker}:{currentTicker.exchange}</span>
        </div>
      </header>

      {/* ═══ Company Info Bar ═══ */}
      <div className="company-bar">
        <div className="company-info">
          <span className="company-name">{currentTicker.name}</span>
          <span className="company-sub">Báo cáo tài chính · Đơn vị: Tỷ VND</span>
        </div>
        <select
          id="ticker-select"
          className="stock-select"
          value={ticker}
          onChange={e => setTicker(e.target.value)}
        >
          {TICKERS.map(t => (
            <option key={t.code} value={t.code}>{t.code} – {t.name}</option>
          ))}
        </select>
      </div>

      {/* ═══ Report Tabs ═══ */}
      <div className="tabs-row">
        <div className="tabs" role="tablist">
          {REPORT_TABS.map(t => (
            <button
              key={t.id}
              id={`tab-${t.id}`}
              role="tab"
              aria-selected={reportType === t.id}
              className={`tab${reportType === t.id ? ' active' : ''}`}
              onClick={() => setReportType(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="period-toggle" role="radiogroup" aria-label="Period filter">
          {PERIOD_FILTERS.map(pf => (
            <button
              key={pf.id}
              id={`period-${pf.id}`}
              role="radio"
              aria-checked={periodFilter === pf.id}
              className={`period-btn${periodFilter === pf.id ? ' active' : ''}`}
              onClick={() => setPeriodFilter(pf.id)}
            >
              {pf.label}
            </button>
          ))}
        </div>
      </div>

      {/* ═══ Stats Bar ═══ */}
      {statSummary && !loading && (
        <div className="stats-bar">
          <div className="stat-chip">
            <span className="stat-label">Kỳ mới nhất</span>
            <span className="stat-value">{statSummary.latestPeriod}</span>
          </div>
          <div className="stat-chip">
            <span className="stat-label">Dòng dữ liệu</span>
            <span className="stat-value">{statSummary.filledCount}/{statSummary.rowCount}</span>
          </div>
          <div className="stat-chip">
            <span className="stat-label">Coverage</span>
            <span className={`stat-value ${statSummary.coverage >= 80 ? 'stat-good' : 'stat-warn'}`}>
              {statSummary.coverage}%
            </span>
          </div>
        </div>
      )}

      {/* ═══ Data Table ═══ */}
      <div className="table-wrap">
        {loading ? (
          <div className="state-msg">
            <div className="loader" />
            <span>Đang tải dữ liệu...</span>
          </div>
        ) : data.length === 0 ? (
          <div className="state-msg">
            <span>Không có dữ liệu {currentTab.label} cho {ticker}</span>
          </div>
        ) : (
          <table className="fin-table">
            <thead>
              <tr>
                <th className="th-item">Chỉ tiêu</th>
                <th className="th-chart" />
                {periods.map(p => <th key={p} className="th-val">{formatPeriodLabel(p)}</th>)}
              </tr>
            </thead>
            <tbody>
              {data.map((row, idx) => {
                if (!isVisible(row)) return null
                const hasChildren = idx < data.length - 1 && data[idx + 1].levels > row.levels
                const isOpen = !!expandedRows[row.item_id]
                const chartVals = periods.map(p => row.periods_data?.[p] || 0)
                const major = isMajorHeading(row)
                const displayLabel = major ? (row.item || '').toUpperCase() : (row.item || '')

                const isL0 = row.levels === 0;
                const isL1 = row.levels === 1;
                const showToggleSpace = isL1 || (row.levels > 0 && hasChildren);

                // Base padding per level
                // L0: 12px
                // L1: 12px + 16px = 28px. If it has toggle (width 14px + 5px gap = 19px), text is at 47px.
                // L2: If we want text to align with L1 text (47px), padding = 47px.
                // L3: 47px + 16px = 63px.
                let padLeft = 12;
                if (row.levels === 1) padLeft = 28;
                if (row.levels >= 2) padLeft = 47 + (row.levels - 2) * 16;

                return (
                  <tr
                    key={row.item_id || idx}
                    className={`fin-row${major ? ' row-major' : ' row-child'} lv${Math.min(row.levels || 0, 4)}`}
                  >
                    <td className="td-item">
                      <div className="item-cell" style={{ paddingLeft: `${padLeft}px` }}>
                        {showToggleSpace && (
                          hasChildren
                            ? <button
                              className="tog"
                              onClick={() => toggle(row.item_id)}
                              aria-label={isOpen ? "Thu gọn" : "Mở rộng"}
                              aria-expanded={isOpen}
                            >
                              {isOpen ? '–' : '+'}
                            </button>
                            : <span className="tog-ph" />
                        )}
                        <span className={`label${isL0 ? ' label-major' : ''}`}>{isL0 ? displayLabel.toUpperCase() : displayLabel}</span>
                      </div>
                    </td>
                    <td className="td-chart">
                      {!major && <MiniBarChart values={chartVals} />}
                    </td>
                    {periods.map(p => {
                      const v = row.periods_data?.[p]
                      return (
                        <td key={p} className={`td-val ${v < 0 ? 'neg' : ''}`}>
                          {formatNumber(v)}
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* ═══ Footer ═══ */}
      <footer className="app-footer">
        <span>Finsang Terminal v2.0 · Powered by Vietcap Data Pipeline</span>
        <span className="footer-source">Source: Version 2 B.L.A.S.T Framework</span>
      </footer>
    </div>
  )
}
