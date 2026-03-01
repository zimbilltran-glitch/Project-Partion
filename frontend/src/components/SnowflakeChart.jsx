/**
 * SnowflakeChart.jsx — V3 P2.3
 * 5-axis radar chart (Snowflake) using pure SVG — zero dependencies.
 * Compatible with Streamlit via Plotly alternative if needed.
 *
 * Props:
 *   scores: { value, future, past, health, dividend }  — each 0.0 to 5.0
 *   size:   number (SVG box size, default 260)
 */

import { useMemo } from 'react'

const AXES = [
    { key: 'value', label: 'Định giá', color: '#9ACA27' },
    { key: 'future', label: 'Tương lai', color: '#26AE50' },
    { key: 'past', label: 'Quá khứ', color: '#26AE50' },
    { key: 'health', label: 'Sức khỏe TC', color: '#26AE50' },
    { key: 'dividend', label: 'Cổ tức', color: '#26AE50' },
]

const N = AXES.length               // 5 axes
const MAX_SCORE = 5.0

// Convert polar → cartesian (0° at top, clockwise)
function polar(cx, cy, r, angleDeg) {
    const rad = ((angleDeg - 90) * Math.PI) / 180
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

// Build SVG polygon points string
function polygonPoints(cx, cy, radius, n, offset = 0) {
    return Array.from({ length: n }, (_, i) => {
        const p = polar(cx, cy, radius, (360 / n) * i + offset)
        return `${p.x},${p.y}`
    }).join(' ')
}

export default function SnowflakeChart({ scores = {}, size = 260 }) {
    const cx = size / 2
    const cy = size / 2
    const maxR = (size / 2) * 0.72   // leave room for labels
    const rings = [1, 2, 3, 4, 5]   // scale rings

    // Build data polygon points
    const dataPoints = useMemo(() => {
        return AXES.map((axis, i) => {
            const score = Math.min(Math.max(scores[axis.key] ?? 0, 0), MAX_SCORE)
            const r = (score / MAX_SCORE) * maxR
            const angle = (360 / N) * i
            const p = polar(cx, cy, r, angle)
            return `${p.x},${p.y}`
        }).join(' ')
    }, [scores, cx, cy, maxR])

    // Label positions (slightly outside maxR)
    const labelR = maxR + 22

    return (
        <div className="snowflake-container" aria-label="Snowflake valuation chart">
            <svg
                width={size}
                height={size}
                viewBox={`0 0 ${size} ${size}`}
                style={{ overflow: 'visible' }}
            >
                {/* Background rings */}
                {rings.map(ring => (
                    <polygon
                        key={ring}
                        points={polygonPoints(cx, cy, (ring / MAX_SCORE) * maxR, N)}
                        fill="none"
                        stroke="rgba(255,255,255,0.07)"
                        strokeWidth="1"
                    />
                ))}

                {/* Axis lines */}
                {AXES.map((axis, i) => {
                    const end = polar(cx, cy, maxR, (360 / N) * i)
                    return (
                        <line
                            key={axis.key}
                            x1={cx} y1={cy}
                            x2={end.x} y2={end.y}
                            stroke="rgba(255,255,255,0.1)"
                            strokeWidth="1"
                        />
                    )
                })}

                {/* Data polygon (glow fill) */}
                <polygon
                    points={dataPoints}
                    fill="rgba(38, 174, 80, 0.18)"
                    stroke="#26AE50"
                    strokeWidth="2"
                    strokeLinejoin="round"
                />

                {/* Data points (dots) */}
                {AXES.map((axis, i) => {
                    const score = Math.min(Math.max(scores[axis.key] ?? 0, 0), MAX_SCORE)
                    const r = (score / MAX_SCORE) * maxR
                    const angle = (360 / N) * i
                    const p = polar(cx, cy, r, angle)
                    return (
                        <circle
                            key={axis.key}
                            cx={p.x} cy={p.y}
                            r={4}
                            fill="#26AE50"
                            stroke="#1A1A1A"
                            strokeWidth="1.5"
                        />
                    )
                })}

                {/* Axis labels */}
                {AXES.map((axis, i) => {
                    const angle = (360 / N) * i
                    const lp = polar(cx, cy, labelR, angle)
                    const textAnchor =
                        Math.abs(lp.x - cx) < 5 ? 'middle'
                            : lp.x < cx ? 'end' : 'start'
                    const score = scores[axis.key] ?? 0
                    return (
                        <g key={axis.key}>
                            <text
                                x={lp.x}
                                y={lp.y - 5}
                                textAnchor={textAnchor}
                                fill="#A0AEC0"
                                fontSize="11"
                                fontFamily="Inter, sans-serif"
                            >
                                {axis.label}
                            </text>
                            <text
                                x={lp.x}
                                y={lp.y + 9}
                                textAnchor={textAnchor}
                                fill="#26AE50"
                                fontSize="12"
                                fontWeight="600"
                                fontFamily="Inter, sans-serif"
                            >
                                {score.toFixed(1)}
                            </text>
                        </g>
                    )
                })}

                {/* Center score */}
                {(() => {
                    const total = Object.values(scores).reduce((a, b) => a + (b ?? 0), 0)
                    const pct = Math.round((total / (MAX_SCORE * N)) * 100)
                    return (
                        <>
                            <text
                                x={cx} y={cy - 6}
                                textAnchor="middle"
                                fill="#FFFFFF"
                                fontSize="18"
                                fontWeight="700"
                                fontFamily="Inter, sans-serif"
                            >
                                {pct}%
                            </text>
                            <text
                                x={cx} y={cy + 11}
                                textAnchor="middle"
                                fill="#A0AEC0"
                                fontSize="10"
                                fontFamily="Inter, sans-serif"
                            >
                                Overall
                            </text>
                        </>
                    )
                })()}
            </svg>
        </div>
    )
}
