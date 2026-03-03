import { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';

export function useAnalysisFetcher(ticker) {
    const [data, setData] = useState({
        inc: [],
        bs: [],
        cf: [],
        ratios: [],
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!ticker) return;
        let cancelled = false;

        async function load() {
            setLoading(true);
            setError(null);

            try {
                const [incRes, bsRes, cfRes, ratioRes] = await Promise.all([
                    supabase.from('income_statement_wide').select('*').eq('stock_name', ticker).order('row_number'),
                    supabase.from('balance_sheet_wide').select('*').eq('stock_name', ticker).order('row_number'),
                    supabase.from('cash_flow_wide').select('*').eq('stock_name', ticker).order('row_number'),
                    supabase.from('financial_ratios_wide').select('*').eq('stock_name', ticker).order('row_number'),
                ]);

                if (incRes.error) throw incRes.error;
                if (bsRes.error) throw bsRes.error;
                if (cfRes.error) throw cfRes.error;
                if (ratioRes.error) throw ratioRes.error;

                if (!cancelled) {
                    setData({
                        inc: incRes.data || [],
                        bs: bsRes.data || [],
                        cf: cfRes.data || [],
                        ratios: ratioRes.data || [],
                    });
                }
            } catch (err) {
                if (!cancelled) setError(err.message);
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => { cancelled = true; };
    }, [ticker]);

    return { ...data, loading, error };
}

export default useAnalysisFetcher;
