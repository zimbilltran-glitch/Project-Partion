import { useMemo } from 'react';

/**
 * Hook to transform raw report data into Recharts-friendly format.
 * @param {Array} allData - The full list of report rows from Supabase.
 * @param {Array} periods - The sorted list of period strings (e.g. ['2023-Q1', ...]).
 * @param {Object} mapping - A map of { display_name: item_id_or_nature }.
 * @returns {Array} - Array of objects like [{ period: 'Q1/23', [display_name]: value, ... }]
 */
export const useAnalysisChartsData = (allData, periods, mapping) => {
    return useMemo(() => {
        if (!allData || !periods || !mapping) return [];

        // 1. Create a lookup for rows by item_id
        const dataMap = {};
        allData.forEach(row => {
            if (row.item_id) {
                dataMap[row.item_id] = row;
            }
        });

        // 2. Pivot data by period
        // We reverse the periods to show oldest on left, newest on right (standard chart)
        const sortedPeriods = [...periods].reverse();

        return sortedPeriods.map(p => {
            const entry = { period: p };

            Object.entries(mapping).forEach(([key, itemId]) => {
                const row = dataMap[itemId];
                // If it's a list of IDs (for summing), handle it
                if (Array.isArray(itemId)) {
                    let sum = 0;
                    itemId.forEach(id => {
                        sum += (dataMap[id]?.periods_data?.[p] || 0);
                    });
                    entry[key] = sum;
                } else {
                    entry[key] = row?.periods_data?.[p] || 0;
                }
            });

            return entry;
        });
    }, [allData, periods, mapping]);
};

export default useAnalysisChartsData;
