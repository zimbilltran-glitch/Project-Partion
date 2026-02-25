# Finsang Project Constitution

## Data Schemas

### 1. OHLCV Price Data Schema (Hourly)
```json
{
  "ticker": "string",
  "timestamp": "datetime",
  "open": "number",
  "high": "number",
  "low": "number",
  "close": "number",
  "volume": "number"
}
```

### 2. Financial Statements Schema (Daily)
```json
{
  "ticker": "string",
  "period": "string", // "Q3.2023", "2023"
  "type": "string", // "balance_sheet", "income_statement", "cash_flow"
  "data": {
    "total_assets": "number",
    "cash_and_equivalents": "number",
    "receivables": "number",
    "inventory": "number",
    "fixed_assets": "number",
    "total_liabilities": "number",
    "short_term_debt": "number",
    "long_term_debt": "number",
    "owner_equity": "number",
    // etc based on vnstock output format
  },
  "last_updated": "datetime"
}
```

## Behavioral Rules
- **Data Fetching:** Do not attempt tick data fetching to avoid rate limits. OHLC data should be fetched on an hourly basis. Financial statement data should be updated daily (every 24h) and only override if changes are detected.
- **Failovers:** If KBSV API fails or changes its signature, fallback directly to `vnstock`'s open-source implementation to fetch data.
- **UI Design:** Prioritize simple, clean, functional UI first with charts. Advanced styling and branding will be layered on later.

## Architectural Invariants
- **Database:** All crawled data MUST be stored in Supabase.
- **Data First:** Payload structures and schemas must be strictly defined before implementing any frontend components or database tables.
- **Architecture First:** Any pipeline or data flow change must be documented in `architecture/` SOPs before script modification.
- **Determinism:** Tool scripts in `tools/` must be pure and atomic where possible. Intermediate files (if any) go to `.tmp/`.
