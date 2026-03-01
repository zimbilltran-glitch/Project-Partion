/**
 * PriceChart.jsx — V3 P2.6
 * OHLCV area chart using pure SVG (no chart library).
 * Shows 2025-2026 closing price with area-fill and hover tooltip.
 *
 * Props:
 *   ohlcv: [ { time, close, volume } ]   ← from useOverviewData
 */

import { useMemo, useState, useRef, useCallback } from 'react'

function formatDate(iso) {
    return new Date(iso).toLocaleDateString('vi-VN', {
        day: '2-digit', month: '2-digit', year: 'numeric'
    })
}
function formatPrice(v) {
    return new Intl.NumberFormat('vi-VN').format(Math.round(v)) + ' ₫'
}

const W = 600, H = 160, PAD = { t: 12, r: 16, b: 28, l: 56 }

export default function PriceChart({ ohlcv = [] }) {
    const [tooltip, setTooltip] = useState(null)
    const svgRef = useRef(null)

    const { points, minP, maxP, path, areaPath, dates } = useMemo(() => {
        if (!ohlcv.length) return { points: [], minP: 0, maxP: 0, path: '', areaPath: '', dates: [] }

        const closes = ohlcv.map(d => d.close)
        const minP = Math.min(...closes)
        const maxP = Math.max(...closes)
        const range = maxP - minP || 1
        const n = closes.length

        const innerW = W - PAD.l - PAD.r
        const innerH = H - PAD.t - PAD.b

        const points = closes.map((v, i) => ({
            x: PAD.l + (i / Math.max(n - 1, 1)) * innerW,
            y: PAD.t + (1 - (v - minP) / range) * innerH,
            v, time: ohlcv[i].time, vol: ohlcv[i].volume,
        }))

        const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
        const areaPathD = `${pathD} L${points[points.length - 1].x.toFixed(1)},${(PAD.t + innerH).toFixed(1)} L${PAD.l},${(PAD.t + innerH).toFixed(1)} Z`

        const dates = [
            ohlcv[0]?.time?.slice(0, 10),
            ohlcv[Math.floor(n / 2)]?.time?.slice(0, 10),
            ohlcv[n - 1]?.time?.slice(0, 10),
        ]

        return { points, minP, maxP, path: pathD, areaPath: areaPathD, dates }
    }, [ohlcv])

    const handleMouseMove = useCallback((e) => {
        if (!points.length || !svgRef.current) return
        const rect = svgRef.current.getBoundingClientRect()
        const mouseX = (e.clientX - rect.left) * (W / rect.width)
        // Find closest point
        let closest = points[0]
        let minDist = Infinity
        for (const p of points) {
            const d = Math.abs(p.x - mouseX)
            if (d < minDist) { minDist = d; closest = p }
        }
        setTooltip({ x: closest.x, y: closest.y, price: closest.v, time: closest.time })
    }, [points])

    const isPositive = points.length >= 2
        ? points[points.length - 1].v >= points[0].v
        : true
    const lineColor = isPositive ? '#26AE50' : '#E53935'
    const areaColor = isPositive ? 'rgba(38,174,80,0.12)' : 'rgba(229,57,53,0.10)'

    if (!ohlcv.length) {
        return (
            <div className="price-chart-wrap">
                <p className="chart-empty">Chưa có dữ liệu giá (chạy fetch_ohlcv_vn30.py để cập nhật)</p>
            </div>
        )
    }

    const innerH = H - PAD.t - PAD.b
    const priceStep = (maxP - minP) / 3 || 1

    return (
        <div className="price-chart-wrap">
            <div className="chart-header-row">
                <span className="chart-title">Giá cổ phiếu (2025 → nay)</span>
                {points.length > 0 && (
                    <span className="chart-latest" style={{ color: lineColor }}>
                        {/* vnstock: price unit = 1 = 1,000 VND. Multiply × 1000 for ₫ display */}
                        {formatPrice(points[points.length - 1].v * 1000)}
                        &nbsp;{isPositive ? '▲' : '▼'}
                        {(((points[points.length - 1].v - points[0].v) / points[0].v) * 100).toFixed(1)}%
                    </span>
                )}
            </div>
            <svg
                ref={svgRef}
                viewBox={`0 0 ${W} ${H}`}
                style={{ width: '100%', height: 'auto', cursor: 'crosshair' }}
                onMouseMove={handleMouseMove}
                onMouseLeave={() => setTooltip(null)}
            >
                {/* Grid lines */}
                {[0, 1, 2, 3].map(i => {
                    const y = PAD.t + (i / 3) * innerH
                    const priceLabel = maxP - i * priceStep
                    return (
                        <g key={i}>
                            <line x1={PAD.l} y1={y} x2={W - PAD.r} y2={y}
                                stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                            <text x={PAD.l - 4} y={y + 4}
                                textAnchor="end" fill="#A0AEC0"
                                fontSize="10" fontFamily="Inter,sans-serif">
                                {/* Show e.g. "62" (means 62,000 VND) */}
                                {priceLabel.toFixed(0)}
                            </text>
                        </g>
                    )
                })}

                {/* Area fill */}
                <path d={areaPath} fill={areaColor} />

                {/* Price line */}
                <path d={path} fill="none" stroke={lineColor} strokeWidth="1.5" strokeLinejoin="round" />

                {/* Date labels */}
                {dates.filter(Boolean).map((d, i) => {
                    const xs = [PAD.l, W / 2, W - PAD.r]
                    return (
                        <text key={i} x={xs[i]} y={H - 4}
                            textAnchor={i === 0 ? 'start' : i === 1 ? 'middle' : 'end'}
                            fill="#A0AEC0" fontSize="10" fontFamily="Inter,sans-serif">
                            {d}
                        </text>
                    )
                })}

                {/* Tooltip */}
                {tooltip && (
                    <g>
                        <line x1={tooltip.x} y1={PAD.t} x2={tooltip.x} y2={H - PAD.b}
                            stroke="rgba(255,255,255,0.2)" strokeWidth="1" strokeDasharray="4,3" />
                        <circle cx={tooltip.x} cy={tooltip.y} r={4}
                            fill={lineColor} stroke="#1A1A1A" strokeWidth="1.5" />
                        <rect x={tooltip.x + 6} y={tooltip.y - 20}
                            width={130} height={36} rx={4}
                            fill="#262626" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
                        <text x={tooltip.x + 12} y={tooltip.y - 7}
                            fill="#FFFFFF" fontSize="11" fontFamily="Inter,sans-serif">
                            {formatDate(tooltip.time)}
                        </text>
                        <text x={tooltip.x + 12} y={tooltip.y + 8}
                            fill={lineColor} fontSize="11" fontWeight="600" fontFamily="Inter,sans-serif">
                            {/* × 1000 to convert vnstock unit → VND */}
                            {formatPrice(tooltip.price * 1000)}
                        </text>
                    </g>
                )}
            </svg>
        </div>
    )
}
