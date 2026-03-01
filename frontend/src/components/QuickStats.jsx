/**
 * QuickStats.jsx — V3 P2.7
 * Grid of key financial metrics for the 360 Overview tab.
 * Layout: 2 rows × 4 cols = 8 stat cards.
 */

function StatCard({ label, value, suffix = '', highlight }) {
    return (
        <div className="stat-card">
            <span className="stat-card-label">{label}</span>
            <span className={`stat-card-value${highlight ? ' stat-card-highlight' : ''}`}>
                {value != null ? `${value}${suffix}` : '—'}
            </span>
        </div>
    )
}

function fmt(v, decimals = 1) {
    if (v == null) return null
    return Number(v).toFixed(decimals)
}

function fmtBig(v) {
    // Format Tỷ VND → "14,850 Tỷ"
    if (v == null) return null
    const tril = v / 1_000_000_000
    if (tril >= 1) return `${new Intl.NumberFormat('vi-VN').format(Math.round(tril))} Tỷ`
    return `${new Intl.NumberFormat('vi-VN').format(Math.round(v))} Tỷ`
}

function fmtPrice(v) {
    if (v == null) return null
    return new Intl.NumberFormat('vi-VN').format(Math.round(v))
}

export default function QuickStats({ overview }) {
    if (!overview) {
        return (
            <div className="quick-stats-grid">
                {Array.from({ length: 8 }).map((_, i) => (
                    <StatCard key={i} label="——" value={null} />
                ))}
            </div>
        )
    }

    const stats = [
        { label: 'P/E (TTM)', value: fmt(overview.pe_ratio), suffix: 'x' },
        { label: 'P/B', value: fmt(overview.pb_ratio), suffix: 'x' },
        { label: 'ROE', value: fmt(overview.score_past > 0 ? overview.score_past * 5 : null), suffix: '%', highlight: overview.score_past >= 3 },
        { label: 'Div Yield', value: fmt(overview.dividend_yield), suffix: '%', highlight: overview.dividend_yield > 2 },
        { label: 'Vốn hóa', value: fmtBig(overview.market_cap), suffix: '' },
        { label: 'EPS (TTM)', value: fmtPrice(overview.eps_ttm), suffix: ' ₫' },
        { label: '52W High', value: fmtPrice(overview.week52_high), suffix: ' ₫' },
        { label: '52W Low', value: fmtPrice(overview.week52_low), suffix: ' ₫' },
    ]

    return (
        <div className="quick-stats-grid">
            {stats.map(s => (
                <StatCard key={s.label} {...s} />
            ))}
        </div>
    )
}
