# V3 Findings Log

> Ghi nhận các phát hiện kỹ thuật trong quá trình triển khai V3.

---

## F-V3-001: Supabase Data Coverage (2026-03-01)

| Table | Rows | Tickers | Status |
|---|---|---|---|
| `balance_sheet` | 119,367 | 31 (VN30+VHC) | ✅ Full |
| `income_statement` | 32,992 | 31 | ✅ Full |
| `cash_flow` | 60,705 | 31 | ✅ Full |
| `financial_ratios` | 39,690 | 31 | ✅ Full |
| `companies` | 34 | 34 | ✅ Full |
| `stock_ohlcv` | 9,455 | 31 (VN30+VHC) | ✅ Full |
| `company_overview` | 31 | 31 (VN30+VHC) | ✅ Full |

## F-V3-002: Existing Frontend Tab Structure

Hiện tại App.jsx có 4 tabs: CDKT, KQKD, LCTT, CSTC.  
V3 sẽ thêm tab "360 Overview" — KHÔNG thay thế tabs hiện tại.

## F-V3-003: Chart Library Choice

Quyết định cuối cùng (Updated 2026-03-01): **Pure SVG** code cứng trực tiếp trong Component.
Lý do:
1. Chart kiểu SWS Snowflake là dạng Radar 5 trục tĩnh, thiết kế rất đơn giản bằng toán học SVG `<polygon>`.
2. Bỏ hoàn toàn dependencies của Plotly (~200KB-1MB), giúp tab Overview load tức thì (0 ms trễ render).
3. Area Chart cho OHLCV cũng dùng `<path>` SVG nội tuyến cực nhẹ, đạt tốc độ render tối đa.
