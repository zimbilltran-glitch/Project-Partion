import React from 'react';
import {
    ComposedChart,
    Bar,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="custom-chart-tooltip">
                <p className="tooltip-label">{label}</p>
                <div className="tooltip-items">
                    {payload.map((entry, index) => (
                        <div key={index} className="tooltip-item" style={{ color: entry.color }}>
                            <span className="item-key">{entry.name}:</span>
                            <span className="item-val">
                                {entry.dataKey.includes('Percent') || entry.dataKey.includes('Ratio') || entry.name.includes('%')
                                    ? `${entry.value.toFixed(2)}%`
                                    : new Intl.NumberFormat('en-US').format(entry.value)}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        );
    }
    return null;
};

const DualAxisChart = ({ data, title, barKey, barName, barColor, lineKey, lineName, lineColor }) => {
    return (
        <div className="chart-card">
            <h3 className="chart-title">{title}</h3>
            <div className="chart-h-container">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                        data={data}
                        margin={{ top: 10, right: 0, left: 0, bottom: 0 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                        <XAxis
                            dataKey="period"
                            stroke="#666"
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            yAxisId="left"
                            stroke="#666"
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(val) => new Intl.NumberFormat('en-US', { notation: 'compact' }).format(val)}
                        />
                        <YAxis
                            yAxisId="right"
                            orientation="right"
                            stroke={lineColor}
                            alpha={0.5}
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(val) => `${val}%`}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend
                            verticalAlign="top"
                            align="right"
                            height={32}
                            iconSize={8}
                            wrapperStyle={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.4px' }}
                        />
                        <Bar
                            yAxisId="left"
                            dataKey={barKey}
                            name={barName}
                            fill={barColor}
                            radius={[4, 4, 0, 0]}
                            barSize={40}
                        />
                        <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey={lineKey}
                            name={lineName}
                            stroke={lineColor}
                            strokeWidth={3}
                            dot={{ r: 4, fill: lineColor, strokeWidth: 0 }}
                            activeDot={{ r: 6 }}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default DualAxisChart;
