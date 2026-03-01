/**
 * CompanyHero.jsx — V3 P2.2
 * Company header section for the 360 Overview tab.
 * Shows: company name, ticker:exchange, sector badge, current price, change, market cap.
 */

const SECTOR_COLORS = {
    bank: '#f59e0b',
    sec: '#8b5cf6',
    normal: '#26AE50',
}
const SECTOR_LABELS = {
    bank: 'Ngân hàng',
    sec: 'Chứng khoán',
    normal: 'Phi tài chính',
}

function formatPrice(v) {
    if (v == null) return '—'
    return new Intl.NumberFormat('vi-VN').format(Math.round(v)) + ' ₫'
}

function formatMarketCap(v) {
    if (v == null) return '—'
    // v is already in Tỷ VND from the API/Database
    return new Intl.NumberFormat('vi-VN').format(Math.round(v)) + ' Tỷ VND'
}

export default function CompanyHero({
    companyName, ticker, exchange = 'HOSE', sector = 'normal',
    currentPrice, priceChange, priceChangePct, marketCap,
}) {
    const isPositive = priceChange > 0
    const changeColor = priceChange == null ? '#A0AEC0'
        : isPositive ? 'var(--s-success)' : 'var(--s-danger)'

    const changeSign = priceChange > 0 ? '+' : ''
    const changeArrow = priceChange > 0 ? '▲' : priceChange < 0 ? '▼' : '–'

    return (
        <div className="company-hero">
            <div className="hero-top">
                <div className="hero-name-wrap">
                    <span className="hero-ticker">{ticker}</span>
                    <span className="hero-exchange">:{exchange}</span>
                    <span
                        className="hero-sector-badge"
                        style={{ backgroundColor: SECTOR_COLORS[sector] || '#26AE50' }}
                    >
                        {SECTOR_LABELS[sector] || sector}
                    </span>
                </div>
                <p className="hero-company-name">{companyName || `CTCP ${ticker}`}</p>
            </div>

            <div className="hero-price-row">
                <span className="hero-price">{formatPrice(currentPrice)}</span>
                {priceChange != null && (
                    <span className="hero-change" style={{ color: changeColor }}>
                        {changeArrow}&nbsp;
                        {changeSign}{formatPrice(Math.abs(priceChange))}
                        &nbsp;({changeSign}{priceChangePct?.toFixed(2)}%)
                    </span>
                )}
            </div>

            {marketCap != null && (
                <p className="hero-marketcap">
                    Vốn hóa: <strong>{formatMarketCap(marketCap)}</strong>
                </p>
            )}
        </div>
    )
}
