import { useEffect, useState, useMemo, Suspense, lazy } from 'react'
import { supabase } from './supabaseClient'
import './App.css'

// V3: 360 Overview tab (lazy-loaded to keep bundle lean)
const OverviewTab = lazy(() => import('./components/OverviewTab'))

// ─── V2 Data Source ────────────────────────────────────────────────────────
// Data synced from Version 2 Parquet pipeline (Vietcap API → Parquet → Supabase).
// Wide views pivot rows via jsonb_object_agg(period, value) = periods_data JSONB.
// Values stored in Tỷ VND. Display in Triệu VND (×1000).
// Phase 2: Ticker list + sector fetched dynamically from Supabase `companies` table.
// ────────────────────────────────────────────────────────────────────────────

// Sector labels for display
const SECTOR_LABELS = {
  bank: 'Ngân hàng',
  sec: 'Chứng khoán',
  normal: 'Phi tài chính',
}

const SECTOR_COLORS = {
  bank: '#f59e0b',
  sec: '#8b5cf6',
  normal: '#10b981',
}

const REPORT_TABS = [
  { id: '360', label: '🔭 360 Overview', table: null },  // V3: Custom overview, no Supabase table
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

// Format: Raw VND (đồng) → Tỷ VND (÷ 1,000,000,000) or keep absolute for ratios
// unit param: row-level unit string for CSTC tab (e.g. 'tỷ đồng', '%', 'lần', 'đồng/cp')
function formatNumber(num, isRatio = false, unit = '') {
  if (num === null || num === undefined) return ''
  if (typeof num !== 'number') return '' // Handle entirely empty cells
  if (num === 0) return '–'
  // For CSTC tab: monetary items (tỷ đồng) still need division, ratios don't
  const isMonetary = unit === 'tỷ đồng' || unit === 'tỷ VND'
  const needsDivision = !isRatio || isMonetary
  const displayNum = needsDivision ? num / 1000000000 : num
  const fractionDigits = (isRatio && !isMonetary) ? 2 : 1
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits,
  }).format(displayNum)
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

  // Phase 2: Dynamic company list + sector from Supabase
  const [companies, setCompanies] = useState([])
  const [sector, setSector] = useState('normal')

  // Load companies on mount
  useEffect(() => {
    async function loadCompanies() {
      const { data: rows, error } = await supabase
        .from('companies')
        .select('*')
        .order('ticker', { ascending: true })
      if (!error && rows) {
        setCompanies(rows)
      }
    }
    loadCompanies()
  }, [])

  // Update sector when ticker changes
  useEffect(() => {
    const company = companies.find(c => c.ticker === ticker)
    setSector(company?.sector || 'normal')
  }, [ticker, companies])

  const currentTicker = useMemo(() => {
    const company = companies.find(c => c.ticker === ticker)
    return company
      ? { code: company.ticker, name: company.company_name, exchange: company.exchange }
      : { code: ticker, name: `CTCP ${ticker}`, exchange: 'HOSE' }
  }, [ticker, companies])

  const currentTab = REPORT_TABS.find(t => t.id === reportType) || REPORT_TABS[0]

  // V3: Skip Supabase fetch entirely when on 360 Overview tab
  useEffect(() => {
    if (reportType === '360') {
      setLoading(false)
      return
    }

    async function fetchData() {
      setLoading(true)

      const { data: reports, error } = await supabase
        .from(currentTab.table)
        .select('*')
        .eq('stock_name', ticker)
        .order('row_number', { ascending: true })
        .limit(10000)

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
          <span className="sector-badge" style={{ backgroundColor: SECTOR_COLORS[sector] || '#10b981' }}>{SECTOR_LABELS[sector] || sector}</span>
          <span className="ticker-badge">{ticker}:{currentTicker.exchange}</span>
        </div>
      </header>

      {/* ═══ Company Info Bar ═══ */}
      <div className="company-bar">
        <div className="company-info">
          <span className="company-name">{currentTicker.name}</span>
          <span className="company-sub">Báo cáo tài chính · Đơn vị: Tỷ VND</span>
        </div>
        <div className="ticker-search-wrapper">
          <input
            list="ticker-list"
            id="ticker-input"
            className="stock-select"
            value={ticker}
            onChange={e => setTicker(e.target.value.toUpperCase())}
            placeholder="Tìm mã CK..."
            autoComplete="off"
          />
          <datalist id="ticker-list">
            {companies.map(c => (
              <option key={c.ticker} value={c.ticker}>{c.company_name}</option>
            ))}
          </datalist>
        </div>
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

      {/* ═══ 360 Overview Tab ═══ */}
      {reportType === '360' ? (
        <Suspense fallback={<div className="state-msg"><div className="loader" /><span>Đang tải 360 Overview...</span></div>}>
          <OverviewTab ticker={ticker} sector={sector} companies={companies} />
        </Suspense>
      ) : (
        /* ═══ Data Table ═══ */
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

                      {periods.map(p => {
                        const v = row.periods_data?.[p]
                        return (
                          <td key={p} className={`td-val ${v < 0 ? 'neg' : ''}`}>
                            {formatNumber(v, currentTab.id === 'CSTC', row.unit || '')}
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
      )}{/* end 360/table conditional */}

      {currentTab.id === 'CSTC' && (
        <div className="cstc-glossary" style={{ margin: '20px', padding: '15px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '13px', color: '#aaa' }}>
          <strong>💡 Chú giải thuật ngữ:</strong>
          <ul style={{ margin: '8px 0 0 15px', padding: 0, lineHeight: '1.6' }}>
            <li><strong>FVTPL</strong> (Fair Value Through Profit or Loss): Các tài sản tài chính ghi nhận thông qua Lãi/Lỗ.</li>
            <li><strong>AFS</strong> (Available For Sale): Các tài sản tài chính sẵn sàng để bán.</li>
            <li><strong>NIM</strong> (Net Interest Margin): Biên lãi ròng.</li>
            <li><strong>TOI</strong> (Total Operating Income): Tổng thu nhập hoạt động.</li>
            <li><strong>NII</strong> (Net Interest Income): Thu nhập lãi thuần.</li>
          </ul>
        </div>
      )}

      {/* ═══ Footer ═══ */}
      <footer className="app-footer">
        <span>Finsang Terminal v2.0 · Powered by Vietcap Data Pipeline</span>
        <span className="footer-source">Source: Version 2 B.L.A.S.T Framework</span>
      </footer>
    </div>
  )
}
