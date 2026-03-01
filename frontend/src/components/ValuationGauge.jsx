/**
 * ValuationGauge.jsx — V3 P2.4
 * Horizontal P/E gauge showing Undervalued / Fair / Overvalued zone.
 * Pure CSS/SVG — no chart library needed.
 *
 * Props:
 *   peRatio:       number | null   — current P/E
 *   industryAvgPE: number          — benchmark (default: 15 for VN30)
 *   sector:        'bank'|'sec'|'normal'
 */

// Sector-specific P/E benchmarks (VN market typical ranges)
const SECTOR_PE_BENCH = {
    bank: 12,   // Banks trade at lower P/Es
    sec: 14,   // Securities
    normal: 16,   // Industrials / consumer
}

const GAUGE_MAX_PE = 40   // clip display at 40x

function getZone(pe, bench) {
    if (pe == null) return 'unknown'
    const ratio = pe / bench
    if (ratio < 0.8) return 'undervalued'
    if (ratio < 1.2) return 'fair'
    return 'overvalued'
}

const ZONE_META = {
    undervalued: { label: 'Định giá thấp', color: '#26AE50', textColor: '#26AE50' },
    fair: { label: 'Định giá hợp lý', color: '#F59E0B', textColor: '#F59E0B' },
    overvalued: { label: 'Định giá cao', color: '#E53935', textColor: '#E53935' },
    unknown: { label: 'Chưa có dữ liệu', color: '#A0AEC0', textColor: '#A0AEC0' },
}

export default function ValuationGauge({ peRatio, sector = 'normal' }) {
    const bench = SECTOR_PE_BENCH[sector] ?? 16
    const zone = getZone(peRatio, bench)
    const meta = ZONE_META[zone]

    // Needle position as % of gauge width (clamp 0–100)
    const needlePct = peRatio != null
        ? Math.min(100, Math.max(0, (peRatio / GAUGE_MAX_PE) * 100))
        : null

    // Zone thresholds as %
    const underEnd = (bench * 0.8 / GAUGE_MAX_PE) * 100   // ~24%
    const fairEnd = (bench * 1.2 / GAUGE_MAX_PE) * 100   // ~48%

    return (
        <div className="valuation-gauge-wrap">
            <div className="gauge-header">
                <span className="gauge-title">Định giá theo P/E</span>
                <span className="gauge-zone-badge" style={{ color: meta.color }}>
                    {meta.label}
                </span>
            </div>

            {/* Gradient bar */}
            <div className="gauge-bar-wrap">
                <div className="gauge-bar" style={{
                    background: `linear-gradient(to right,
            rgba(38,174,80,0.7)     0%,
            rgba(38,174,80,0.7)     ${underEnd}%,
            rgba(245,158,11,0.7)    ${underEnd}%,
            rgba(245,158,11,0.7)    ${fairEnd}%,
            rgba(229,57,53,0.7)     ${fairEnd}%,
            rgba(229,57,53,0.7)     100%)`,
                }}>
                    {/* Needle */}
                    {needlePct != null && (
                        <div
                            className="gauge-needle"
                            style={{ left: `${needlePct}%`, backgroundColor: meta.color }}
                            title={`P/E = ${peRatio?.toFixed(1)}x`}
                        />
                    )}
                </div>

                {/* Zone labels below bar */}
                <div className="gauge-labels">
                    <span style={{ width: `${underEnd}%`, color: '#26AE50' }}>Thấp</span>
                    <span style={{ width: `${fairEnd - underEnd}%`, color: '#F59E0B' }}>Hợp lý</span>
                    <span style={{ width: `${100 - fairEnd}%`, color: '#E53935' }}>Cao</span>
                </div>
            </div>

            {/* P/E detail row */}
            <div className="gauge-detail">
                <span className="gauge-detail-item">
                    P/E hiện tại: <strong style={{ color: meta.color }}>
                        {peRatio != null ? `${peRatio.toFixed(1)}x` : '—'}
                    </strong>
                </span>
                <span className="gauge-detail-item">
                    Chuẩn ngành: <strong style={{ color: '#A0AEC0' }}>{bench}x</strong>
                </span>
                {peRatio != null && (
                    <span className="gauge-detail-item">
                        {zone === 'undervalued'
                            ? `Thấp hơn chuẩn ${((1 - peRatio / bench) * 100).toFixed(0)}%`
                            : zone === 'overvalued'
                                ? `Cao hơn chuẩn ${((peRatio / bench - 1) * 100).toFixed(0)}%`
                                : 'Trong vùng hợp lý'}
                    </span>
                )}
            </div>
        </div>
    )
}
