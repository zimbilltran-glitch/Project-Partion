/**
 * useOverviewData.js — V3 P2.8
 * Custom hook: Fetch company_overview + stock_ohlcv from Supabase.
 * Used by OverviewTab and all sub-components on the 360 tab.
 */
import { useState, useEffect } from 'react'
import { supabase } from '../supabaseClient'

export function useOverviewData(ticker) {
    const [overview, setOverview] = useState(null)
    const [ohlcv, setOhlcv] = useState([])
    const [ratios, setRatios] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!ticker) return
        let cancelled = false

        async function load() {
            setLoading(true)
            setError(null)

            try {
                // 1. company_overview (single row)
                const { data: ovData, error: ovErr } = await supabase
                    .from('company_overview')
                    .select('*')
                    .eq('ticker', ticker)
                    .maybeSingle()
                if (ovErr) throw ovErr

                // 2. OHLCV — latest 365 trading days
                const { data: priceData, error: priceErr } = await supabase
                    .from('stock_ohlcv')
                    .select('time,open,high,low,close,volume')
                    .eq('stock_name', ticker)
                    .gte('time', '2025-01-01')
                    .order('time', { ascending: true })
                    .limit(500)
                if (priceErr) throw priceErr

                // 3. Financial ratios (for Snowflake score display + checklists)
                //    Pull latest annual period from financial_ratios_wide view
                const { data: ratioData, error: ratioErr } = await supabase
                    .from('financial_ratios_wide')
                    .select('item_id,item,periods_data,unit,levels')
                    .eq('stock_name', ticker)
                    .order('row_number', { ascending: true })
                    .limit(200)
                if (ratioErr) throw ratioErr

                if (!cancelled) {
                    setOverview(ovData)          // null if not yet fetched by backend
                    setOhlcv(priceData || [])
                    setRatios(ratioData || [])
                }
            } catch (e) {
                if (!cancelled) setError(e.message)
            } finally {
                if (!cancelled) setLoading(false)
            }
        }

        load()
        return () => { cancelled = true }
    }, [ticker])

    // ── Derived helpers ─────────────────────────────────────────────────────

    // Get latest close price from OHLCV
    // vnstock returns prices in 1,000 VND units (close=62 → 62,000 VND)
    const _rawClose = ohlcv.length > 0 ? ohlcv[ohlcv.length - 1]?.close : null
    const latestPrice = _rawClose != null
        ? _rawClose * 1000
        : overview?.current_price ?? null

    // Get price change (last 2 rows) — also in ×1000 VND
    const _rawPrev = ohlcv.length >= 2 ? ohlcv[ohlcv.length - 2].close : null
    const _rawDiff = _rawClose != null && _rawPrev != null ? _rawClose - _rawPrev : null
    const priceChange = _rawDiff != null ? _rawDiff * 1000 : null
    const priceChangePct = _rawDiff != null && _rawPrev != null
        ? (_rawDiff / _rawPrev) * 100
        : null

    // Helper: get latest period value from financial_ratios_wide periods_data
    function getRatioValue(itemId) {
        const row = ratios.find(r => r.item_id === itemId)
        if (!row?.periods_data) return null
        // Get latest annual (4-digit year key), fallback to quarterly
        const keys = Object.keys(row.periods_data).sort().reverse()
        const yearKey = keys.find(k => /^\d{4}$/.test(k))
        const key = yearKey || keys[0]
        return key ? row.periods_data[key] : null
    }

    return {
        overview,
        ohlcv,
        ratios,
        loading,
        error,
        latestPrice,
        priceChange,
        priceChangePct,
        getRatioValue,
    }
}
