/**
 * OverviewTab.jsx — V3 P2.1
 * Main container for the "360 Overview" tab.
 * Orchestrates: CompanyHero + SnowflakeChart + QuickStats +
 *               ValuationGauge + ChecklistCards + PriceChart
 *
 * Props:
 *   ticker:    string   — current stock ticker (e.g. 'VHC')
 *   sector:    string   — 'normal' | 'bank' | 'sec'
 *   companies: array    — from Supabase `companies` table (for company name)
 */

import CompanyHero from './CompanyHero'
import SnowflakeChart from './SnowflakeChart'
import QuickStats from './QuickStats'
import ValuationGauge from './ValuationGauge'
import ChecklistCards from './ChecklistCards'
import PriceChart from './PriceChart'
import { useOverviewData } from '../hooks/useOverviewData'

export default function OverviewTab({ ticker, sector, companies = [] }) {
    const {
        overview, ohlcv, loading, error,
        latestPrice, priceChange, priceChangePct, getRatioValue,
    } = useOverviewData(ticker)

    // Get company name from companies list (already in App.jsx memory)
    const company = companies.find(c => c.ticker === ticker)
    const companyName = company?.company_name ?? overview?.industry ?? `CTCP ${ticker}`
    const exchange = company?.exchange ?? 'HOSE'

    // Snowflake scores from company_overview (or zeros while loading)
    const scores = {
        value: overview?.score_value ?? 0,
        future: overview?.score_future ?? 0,
        past: overview?.score_past ?? 0,
        health: overview?.score_health ?? 0,
        dividend: overview?.score_dividend ?? 0,
    }

    // ── Loading state ────────────────────────────────────────────────────────
    if (loading) {
        return (
            <div className="overview-tab">
                <div className="overview-loading">
                    <div className="loader" />
                    <span>Đang tải 360 Overview cho <strong>{ticker}</strong>...</span>
                </div>
            </div>
        )
    }

    // ── Error state ──────────────────────────────────────────────────────────
    if (error) {
        return (
            <div className="overview-tab">
                <div className="overview-error">
                    <span>⚠️ Lỗi tải dữ liệu: {error}</span>
                </div>
            </div>
        )
    }

    // ── No overview data yet ─────────────────────────────────────────────────
    // company_overview table may be empty until fetch_company_overview.py runs
    const hasOverview = overview != null

    return (
        <div className="overview-tab">

            {/* ═══ Hero ═══ */}
            <CompanyHero
                companyName={companyName}
                ticker={ticker}
                exchange={exchange}
                sector={sector}
                currentPrice={latestPrice}
                priceChange={priceChange}
                priceChangePct={priceChangePct}
                marketCap={overview?.market_cap}
            />

            {/* ═══ Snowflake + Quick Stats (side-by-side) ═══ */}
            <div className="overview-mid-row">
                <div className="snowflake-panel">
                    <p className="panel-label">Phân tích 5 chiều</p>
                    <SnowflakeChart scores={scores} size={240} />
                    {!hasOverview && (
                        <p className="data-note">
                            ⚙️ Chạy <code>calc_snowflake.py</code> để cập nhật điểm số
                        </p>
                    )}
                </div>
                <div className="stats-panel">
                    <p className="panel-label">Chỉ số chính</p>
                    <QuickStats overview={overview} />
                </div>
            </div>

            {/* ═══ Valuation Gauge ═══ */}
            <div className="overview-section">
                <ValuationGauge
                    peRatio={overview?.pe_ratio}
                    sector={sector}
                />
            </div>

            {/* ═══ Checklist Cards ═══ */}
            <div className="overview-section">
                <ChecklistCards
                    overview={overview}
                    getRatioValue={getRatioValue}
                    sector={sector}
                    loading={!hasOverview}
                />
            </div>

            {/* ═══ Price Chart ═══ */}
            <div className="overview-section">
                <PriceChart ohlcv={ohlcv} />
            </div>

            {/* ═══ Data freshness footer ═══ */}
            {hasOverview && overview.updated_at && (
                <p className="overview-updated">
                    Cập nhật lần cuối: {new Date(overview.updated_at).toLocaleDateString('vi-VN')}
                    &nbsp;·&nbsp;Nguồn: Vietcap / VNDirect
                </p>
            )}
        </div>
    )
}
