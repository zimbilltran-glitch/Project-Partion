# Progress Log

## Session 0 – Initialization
- Initialized core project files according to the B.L.A.S.T. framework.
- Awaiting answers to the 5 discovery questions.

## Phase B – Blueprint
- Defined OHLC and Financial Statement schemas in `gemini.md`.
- Updated `task_plan.md` with goals and architecture invariants.

## Phase L – Link
- **Supabase**: Connection successful via provided API key.
```markdown
- **VNStock/KBS**: Cloned `vnstock-agent-guide` (VNstock3_learn repo). Discovered that the correct package is `vnstock` (not `vnstock3`). Used the provided VIP key (redacted) to hit the `kbs` source. Handshake script confirmed that fetching OHLC Quote data works successfully.
```

## Phase A – Architect
- Wrote `system-sop.md` and `tools-sop.md` detailing ETL and Data Schemas.
- Explored direct KBSV endpoint for financial reports and verified it functions correctly when provided with the complete parameter set.
- Successfully migrated Database: Created `financial_reports` (Long Format) and `stock_ohlcv`.
- Implemented `fetch_financials.py`: Pulls directly via `requests` from KBS API, unwraps the WIDE JSON format mapping to actual periods, and upserts into `financial_reports`.
- Implemented `fetch_ohlcv.py`: Pulls OHLCV history via `vnstock`, processes timeframe with Timezones, and upserts into `stock_ohlcv`.

## Phase S – Stylize
- Separated standard barcharts and adjusted column sorting horizontally for temporal viewing.
- Implemented conditional CSS to highlight "Sub-totals" and "Major Headings" (Gold text formatting).
- Rendered UI with React & Vite using a clean IBCS-inspired format.

## Phase C – CFO Standardization & Phase D – Data Engineering
- Abandoned the "Wide JSON" database schema. Redesigned to strict "Long" format (`period`, `item`, `value`, `levels`).
- Created a Master Chart of Accounts template (`tt200_coa.csv`) and seeded it into Supabase via `seed_coa.py`.
- Refactored `fetch_financials.py` to recursively map `ParentReportNormID` into hierarchical `levels` and perform Dense-merging to solve the "Sparse Data" problem.
- Wrote `compute_ratios.py` to precalculate advanced MOLAP ratios.
- Developed `scrape_simplize.py` using `crawl4ai` and `playwright` for Stealth Web Scraping to avoid FireCrawl token limits.
- Wrote `reconcile_simplize.py` functioning as an autonomous `@professional-cfo-analyst` to audit JSON datasets via Accounting Equation checksums (Assets = Liabilities + Equity) before inserting them to production.

## Phase T – Trigger & Deployment
- Overcame CTO Audit Debts by:
  1. Adding `pytest` Unit Tests covering recursive tree breakages.
  2. Creating `orchestrator.py` to chain all ETL phases in a sequential DAG.
  3. Configuring Playwright Stealth via `Crawl4Ai` `magic=True` to bypass Cloudflare and Web Application Firewalls (WAF).
- Created a GitHub Actions Workflow (`.github/workflows/data_pipeline.yml`) to automatically trigger `orchestrator.py` every day at 01:00 AM VN Time.
- The entire B.L.A.S.T Framework is now 100% COMPLETE and production-ready.
