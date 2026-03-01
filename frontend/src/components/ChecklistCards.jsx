/**
 * ChecklistCards.jsx — V3 P2.5
 * Pass/fail checklist cards for the 360 Overview tab.
 * Checks are derived from company_overview + financial_ratios data.
 *
 * Props:
 *   overview:      company_overview row (may be null)
 *   getRatioValue: fn(itemId) → number|null from financial_ratios_wide
 *   sector:        'bank' | 'sec' | 'normal'
 */

function CheckItem({ passed, label, detail, loading }) {
    if (loading) {
        return (
            <div className="check-item check-loading">
                <span className="check-icon">⏳</span>
                <div className="check-text">
                    <span className="check-label">{label}</span>
                </div>
            </div>
        )
    }

    const icon = passed === true ? '✅' : passed === false ? '❌' : '➖'
    const cls = passed === true ? 'check-pass' : passed === false ? 'check-fail' : 'check-neutral'

    return (
        <div className={`check-item ${cls}`}>
            <span className="check-icon">{icon}</span>
            <div className="check-text">
                <span className="check-label">{label}</span>
                {detail && <span className="check-detail">{detail}</span>}
            </div>
        </div>
    )
}

// ── Helper: safe number ───────────────────────────────────────────────────────
function num(v) {
    const n = parseFloat(v)
    return isNaN(n) ? null : n
}

// ── Build checks per sector ───────────────────────────────────────────────────
function buildChecks(overview, getRatioValue, sector) {
    const pe = num(overview?.pe_ratio)
    const pb = num(overview?.pb_ratio)
    const divY = num(overview?.dividend_yield)
    const mktCap = num(overview?.market_cap)

    // Ratios from financial_ratios_wide (item_id from metrics.py)
    // Growth YoY from g7_1, g7_2
    const revGrowth = getRatioValue('g7_1')   // % YoY revenue growth
    const lnGrowth = getRatioValue('g7_2')   // % YoY net profit growth
    // Cash flow from g4_1 (LCTT từ HĐKD)
    const ocf = getRatioValue('g4_1')

    // Snowflake scores (if available)
    const scoreHealth = num(overview?.score_health)
    const scoreFuture = num(overview?.score_future)

    const SECTOR_PE = { bank: 12, sec: 14, normal: 16 }
    const benchPE = SECTOR_PE[sector] ?? 16

    if (sector === 'bank') {
        return [
            {
                label: 'P/B thấp hơn trung bình ngành',
                passed: pb != null ? pb < 1.5 : null,
                detail: pb != null ? `P/B = ${pb.toFixed(1)}x (chuẩn: < 1.5x)` : null,
            },
            {
                label: 'Lợi nhuận tăng trưởng',
                passed: lnGrowth != null ? lnGrowth > 0 : null,
                detail: lnGrowth != null ? `Tăng trưởng LN: ${lnGrowth > 0 ? '+' : ''}${lnGrowth?.toFixed(1)}% YoY` : null,
            },
            {
                label: 'Sức khỏe tài chính tốt',
                passed: scoreHealth != null ? scoreHealth >= 3 : null,
                detail: scoreHealth != null ? `Điểm sức khỏe: ${scoreHealth.toFixed(1)}/5` : null,
            },
            {
                label: 'Cổ tức ổn định',
                passed: divY != null ? divY > 0 : null,
                detail: divY != null ? `Tỷ suất cổ tức: ${divY.toFixed(1)}%` : null,
            },
        ]
    }

    if (sector === 'sec') {
        return [
            {
                label: 'P/E thấp hơn trung bình ngành',
                passed: pe != null ? pe < benchPE : null,
                detail: pe != null ? `P/E = ${pe.toFixed(1)}x (chuẩn: ${benchPE}x)` : null,
            },
            {
                label: 'Doanh thu tăng trưởng',
                passed: revGrowth != null ? revGrowth > 0 : null,
                detail: revGrowth != null ? `Tăng trưởng DT: ${revGrowth > 0 ? '+' : ''}${revGrowth?.toFixed(1)}% YoY` : null,
            },
            {
                label: 'Lợi nhuận tăng trưởng',
                passed: lnGrowth != null ? lnGrowth > 0 : null,
                detail: lnGrowth != null ? `Tăng trưởng LN: ${lnGrowth > 0 ? '+' : ''}${lnGrowth?.toFixed(1)}% YoY` : null,
            },
            {
                label: 'Triển vọng tăng trưởng tốt',
                passed: scoreFuture != null ? scoreFuture >= 3 : null,
                detail: scoreFuture != null ? `Điểm tương lai: ${scoreFuture.toFixed(1)}/5` : null,
            },
        ]
    }

    // Normal (non-financial)
    return [
        {
            label: 'P/E thấp hơn trung bình ngành',
            passed: pe != null ? pe < benchPE : null,
            detail: pe != null ? `P/E = ${pe.toFixed(1)}x (chuẩn VN30: ${benchPE}x)` : null,
        },
        {
            label: 'Doanh thu tăng trưởng',
            passed: revGrowth != null ? revGrowth > 0 : null,
            detail: revGrowth != null ? `${revGrowth > 0 ? '+' : ''}${revGrowth?.toFixed(1)}% YoY` : null,
        },
        {
            label: 'Lợi nhuận tăng trưởng',
            passed: lnGrowth != null ? lnGrowth > 0 : null,
            detail: lnGrowth != null ? `${lnGrowth > 0 ? '+' : ''}${lnGrowth?.toFixed(1)}% YoY` : null,
        },
        {
            label: 'Dòng tiền hoạt động dương',
            passed: ocf != null ? ocf > 0 : null,
            detail: ocf != null
                ? `LCTT HĐKD: ${ocf > 0 ? '+' : ''}${(ocf / 1_000_000_000).toFixed(0)} Tỷ VND`
                : null,
        },
        {
            label: 'Cổ tức có thanh toán',
            passed: divY != null ? divY > 0 : null,
            detail: divY != null ? `Tỷ suất cổ tức: ${divY.toFixed(1)}%` : null,
        },
        {
            label: 'Sức khỏe tài chính tốt',
            passed: scoreHealth != null ? scoreHealth >= 3 : null,
            detail: scoreHealth != null ? `Điểm sức khỏe: ${scoreHealth.toFixed(1)}/5` : null,
        },
    ]
}

// ── Main component ────────────────────────────────────────────────────────────
export default function ChecklistCards({ overview, getRatioValue, sector = 'normal', loading = false }) {
    const checks = overview || !loading
        ? buildChecks(overview, getRatioValue, sector)
        : Array.from({ length: 6 }, (_, i) => ({ label: `Đang tải kiểm tra ${i + 1}...` }))

    const passed = checks.filter(c => c.passed === true).length
    const total = checks.filter(c => c.passed != null).length

    return (
        <div className="checklist-section">
            <div className="checklist-header">
                <span className="checklist-title">Kiểm tra sức khỏe tài chính</span>
                {total > 0 && (
                    <span className="checklist-score">
                        {passed}/{total} đạt
                    </span>
                )}
            </div>
            <div className="checklist-grid">
                {checks.map((c, i) => (
                    <CheckItem key={i} {...c} loading={loading && !overview} />
                ))}
            </div>
        </div>
    )
}
