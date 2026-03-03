import React from 'react';
import {
    BarChart,
    Bar,
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
                                {new Intl.NumberFormat('en-US').format(entry.value)}
                                {entry.unit || ''}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        );
    }
    return null;
};

const CompareBarChart = ({ data, title, bars }) => {
    return (
        <div className="chart-card">
            <h3 className="chart-title">{title}</h3>
            <div className="chart-h-container">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
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
                            stroke="#666"
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(val) => new Intl.NumberFormat('en-US', { notation: 'compact' }).format(val)}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend
                            verticalAlign="top"
                            align="right"
                            height={32}
                            iconSize={8}
                            wrapperStyle={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.4px' }}
                        />
                        {bars.map((bar, idx) => (
                            <Bar
                                key={idx}
                                dataKey={bar.key}
                                name={bar.name}
                                fill={bar.color}
                                radius={[4, 4, 0, 0]}
                            />
                        ))}
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default CompareBarChart;
