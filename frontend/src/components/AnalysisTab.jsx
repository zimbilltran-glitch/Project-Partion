import React, { useMemo } from 'react';
import useAnalysisFetcher from '../hooks/useAnalysisFetcher';
import useAnalysisChartsData from '../hooks/useAnalysisChartsData';
import { SECTOR_MAPPINGS } from '../utils/chartMappings';

// Chart Components
import CompareBarChart from './charts/CompareBarChart';
import TrendLineChart from './charts/TrendLineChart';
import StackedAreaChart from './charts/StackedAreaChart';
import DualAxisChart from './charts/DualAxisChart';

const AnalysisTab = ({ ticker, sector, periods: propPeriods }) => {
    const { inc, bs, cf, ratios, loading, error } = useAnalysisFetcher(ticker);

    // Consolidate all report rows into one list for the transformer
    const combinedData = useMemo(() => {
        return [...inc, ...bs, ...cf, ...ratios];
    }, [inc, bs, cf, ratios]);

    // Derive periods from combinedData if not passed as prop
    const periods = useMemo(() => {
        if (propPeriods && propPeriods.length > 0) return propPeriods;
        const allSet = new Set();
        combinedData.forEach(row => {
            if (row.periods_data) {
                Object.keys(row.periods_data).forEach(p => allSet.add(p));
            }
        });
        // Sort descending (latest first) and slice last 12
        return Array.from(allSet).sort().reverse().slice(0, 12);
    }, [combinedData, propPeriods]);

    const mappings = SECTOR_MAPPINGS[sector] || SECTOR_MAPPINGS.normal;

    // 1. Profit & Loss Performance
    const perfData = useAnalysisChartsData(combinedData, periods, mappings.income_performance || {});

    // 2. Asset Structure
    const assetData = useAnalysisChartsData(combinedData, periods, mappings.asset_structure || {});

    // 3. Growth / Credit
    const growthData = useAnalysisChartsData(combinedData, periods, mappings.growth || mappings.credit_growth || {});

    // 4. Capital / Efficiency
    const capData = useAnalysisChartsData(combinedData, periods, mappings.capital_structure || mappings.efficiency || {});

    // 5. Revenue Structure (Securities)
    const revData = useAnalysisChartsData(combinedData, periods, mappings.revenue_structure || {});

    // 6. NPL Structure (Bank)
    const nplData = useAnalysisChartsData(combinedData, periods, mappings.npl_structure || {});

    if (loading) return (
        <div className="state-msg">
            <div className="loader" />
            <span>Đang chuẩn bị dữ liệu phân tích đồ thị...</span>
        </div>
    );

    if (error) return (
        <div className="state-msg">
            <span>⚠️ Lỗi: {error}</span>
        </div>
    );

    return (
        <div className="analysis-tab">
            <div className="charts-grid">

                {/* ROW 1: PERFORMANCE & GROWTH */}
                {sector === 'normal' ? (
                    <>
                        <DualAxisChart
                            data={perfData}
                            title="Hiệu quả kinh doanh"
                            barKey="Doanh thu thuần"
                            barName="Doanh thu"
                            barColor="#3b82f6"
                            lineKey="Biên lãi ròng"
                            lineName="Biên lãi ròng (%)"
                            lineColor="#10b981"
                        />
                        <TrendLineChart
                            data={growthData}
                            title="Tốc độ tăng trưởng"
                            lines={[
                                { key: 'Tăng trưởng DTT (%)', name: 'g(DTT)', color: '#3b82f6' },
                                { key: 'Tăng trưởng Lãi ròng (%)', name: 'g(LNST)', color: '#f59e0b' }
                            ]}
                        />
                    </>
                ) : sector === 'bank' ? (
                    <>
                        <DualAxisChart
                            data={perfData}
                            title="Thu nhập & NIM"
                            barKey="Tổng thu nhập"
                            barName="Tổng thu nhập"
                            barColor="#f59e0b"
                            lineKey="NIM (%)"
                            lineName="NIM (%)"
                            lineColor="#3b82f6"
                        />
                        <DualAxisChart
                            data={growthData}
                            title="Tín dụng & Tăng trưởng"
                            barKey="Cho vay khách hàng"
                            barName="Cho vay"
                            barColor="#8b5cf6"
                            lineKey="g(TOI) (%)"
                            lineName="g(TOI) %"
                            lineColor="#f97316"
                        />
                    </>
                ) : (
                    /* Securities */
                    <>
                        <DualAxisChart
                            data={perfData}
                            title="Hiệu quả KD Chứng khoán"
                            barKey="Tổng doanh thu"
                            barName="Doanh thu"
                            barColor="#8b5cf6"
                            lineKey="Biên lãi ròng (%)"
                            lineName="Biên lãi ròng (%)"
                            lineColor="#10b981"
                        />
                        <TrendLineChart
                            data={growthData}
                            title="Tăng trưởng"
                            lines={[
                                { key: 'ROE', name: 'ROE', color: '#ef4444' },
                                { key: 'ROA', name: 'ROA', color: '#3b82f6' }
                            ]}
                        />
                        {mappings.revenue_structure && (
                            <StackedAreaChart
                                data={revData}
                                title="Cơ cấu Doanh thu"
                                areas={Object.keys(mappings.revenue_structure).map((name, i) => ({
                                    key: name,
                                    name: name,
                                    color: ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b'][i % 4]
                                }))}
                            />
                        )}
                    </>
                )}

                {/* ROW 2: STRUCTURE & EFFICIENCY */}
                {mappings.asset_structure && (
                    <StackedAreaChart
                        data={assetData}
                        title="Cơ cấu Tài sản"
                        areas={Object.keys(mappings.asset_structure).map((name, i) => ({
                            key: name,
                            name: name,
                            color: [
                                '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#f97316', '#ef4444', '#64748b'
                            ][i % 7]
                        }))}
                    />
                )}

                {(sector === 'normal' || sector === 'sec') && mappings.capital_structure && (
                    <StackedAreaChart
                        data={capData}
                        title="Cơ cấu Nguồn vốn"
                        areas={Object.keys(mappings.capital_structure).map((name, i) => ({
                            key: name,
                            name: name,
                            color: [
                                '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#f97316', '#ef4444', '#64748b'
                            ][i % 7]
                        }))}
                    />
                )}

                {sector === 'bank' && (
                    <>
                        <TrendLineChart
                            data={capData}
                            title="Hiệu quả & Chi phí"
                            lines={[
                                { key: 'CASA (%)', name: 'CASA', color: '#10b981' },
                                { key: 'COF (%)', name: 'COF (Giá vốn)', color: '#8b5cf6' },
                                { key: 'YOEA (%)', name: 'YOEA (Lợi suất)', color: '#f59e0b' }
                            ]}
                        />
                        {/* Adding NPL Chart for Bank */}
                        <TrendLineChart
                            data={nplData}
                            title="Chất lượng nợ xấu"
                            lines={[
                                { key: 'Tỷ lệ nợ xấu (%)', name: 'NPL (%)', color: '#ef4444' }
                            ]}
                        />
                    </>
                )}

            </div>
        </div>
    );
};

export default AnalysisTab;
