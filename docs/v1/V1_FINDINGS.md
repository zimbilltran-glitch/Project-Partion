# Findings

## Sources
- **Data Source**: KBSV API / `vnstock` library (Python). The user has history with `vnstock_data` and fetching OHLCV and Financial Reports.
- **Samples**: Provided sample images show "Cấu trúc Tài sản" (Asset Structure) and "Cấu trúc Nguồn vốn" (Capital Structure) represented as stacked bar charts across quarters (Q3.22 - Q3.25). Another table shows detailed P&L and Balance Sheet numbers.
- **Database**: Supabase.

## Constraints
- **Rate limiting**: Tick data requests will fail/block. Must fetch OHLC data hourly at most.
- **Update Frequency**: Financial reports are to be updated every 24 hours only.
- **Resilience**: Must support a fallback to open source `vnstock` if direct KBS API reverse engineering fails.

## Open Questions
- Do we have the Supabase Database credentials (URL and anon/service role key) ready in the `.env` file?
- Which frontend framework should we use for the "simple UI" (Next.js, Vite + React, or pure HTML/JS)?
- What charting library should we use? (Recommendation: Recharts or Chart.js for financial stacked bars).

## 🕵️‍♂️ CTO Audit Report (Score: 85)
- **Status:** READY FOR PRODUCTION
- **Strengths:** Excellent Database pivot (Wide to Long) resolving key scalability issues. Dense Data Merging via `tt200_coa` completely neutralizes API sparsity risks. Zero-Trust scraping architecture utilizing mathematical Checksums guarantees data integrity before DB injection.
- **Weaknesses/Debt:** 
  1. Reliance on Firecrawl introduces severe API token burn risks at scale. 
  2. Scripts are currently decoupled; a mature orchestration layer (DAG/Cron) is missing.
  3. Lacks Unit Tests (`pytest`) to mock extreme API failures for the recursive node-mapping functions.
- **Timestamp:** 2026-02-22T22:33:43+07:00
- **Auditor:** @cto-mentor-supervisor

## 🔄 V2 Pivot: Fireant Data Reverse-Engineering Findings
- **Endpoint Structure**: Fireant uses two distinct endpoints depending on the request type: `full-financial-reports` (Tree-structured arrays) and `financial-reports` (Matrix/Flat structures).
- **Cash Flow Discovery**: Contrary to initial testing, Cash Flow (LCTT_TT, LCTT_GT) *does* exist on the `full-financial-reports` endpoint. The initial zero-row bug was caused by an out-of-sync COA `report_type` string in the database (`LCTT_GT`) versus the Python script attempting to query the deprecated `LCTT_GIAN_TIEP`.
- **Duplicate Item Names**: Fireant's JSON payload reuses identical strings (e.g., `- Nguyên giá`) across different sections (Tangible vs. Intangible assets). A standard dictionary lookup will blindly overwrite the first occurrence, destroying data density.
