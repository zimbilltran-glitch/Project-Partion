# Finsang Master Challenges — Engineering Solutions Log

Centralized log of critical technical hurdles encountered during the development of Finsang, including their root causes and verified solutions.

---

## 📋 High-Impact Solutions (Must Read)

### 1. Data Shifting & Index Drift (Vietcap API)
- **Symptom:** Fixed values (e.g., 192.10M) appearing across all quarters for specific fields like "Phải trả khác".
- **Root Cause:** Using `enumerate(schema_fields)` created a relative index. Since the schema was a subset (122 fields) of the full API structure (~130 fields), the mapping drifted.
- **Solution:** Use strictly **absolute indexing** via `field.get("row_number")` from the canonical schema.
- **Level:** CRITICAL.

### 2. `slugify()` String Length Mismatch
- **Symptom:** `ValueError` during schema extraction due to Vietnamese character multi-byte counts.
- **Root Cause:** Standard string translation didn't handle decomposed Unicode correctly.
- **Solution:** Standardize with `unicodedata.normalize("NFD", text)` and strip marks.
- **Level:** HIGH.

### 3. Rich Markup Terminal Crash
- **Symptom:** `MarkupError` when displaying CFO badges with square brackets.
- **Root Cause:** `rich` library interprets `[]` as markup tags.
- **Solution:** Escape with backslashes `\[]` and use raw f-strings `rf""`.
- **Level:** MEDIUM.

### 4. Parquet Logic Drift
- **Symptom:** Missing periods or incorrect sorting in the UI.
- **Root Cause:** Hive partitioning structure was inconsistent across Tickers.
- **Solution:** Unified Hive structure: `data/financial/{ticker}/period={type}/sheet={id}/{filename}.parquet`.
- **Level:** HIGH.

### 5. Positional Mapping Anti-Pattern (V5)
- **Symptom:** Core metrics (like Net Income) showing EPS values or other unrelated data.
- **Root Cause:** API keys (`isa1, bsa1`) are strictly positional indexes, not semantic labels. If a company lacks a row, everything shifts.
- **Solution:** Switched to **Exact Ground Truth Mapping**. Hardcoded canonical keys based on direct visual confirmation from audited statements.
- **Level:** CATASTROPHIC.

### 6. Synchronous Pipeline & Huge Schema Bottlenecks (V5)
- **Symptom:** `v5_full_resync.py` taking 45+ minutes to run 30 tickers, terminal hanging, massive RAM usage.
- **Root Cause:** `subprocess.run` forcing OS to spin up 31 Python interpreters. `golden_schema.json` bloat (1MB) loaded on every cycle. Parquet disk I/O in the critical path.
- **Solution (Pending Tech Debt):** Needs an Async/ThreadPool refactor, stripping schema to a `lite_schema.json`, and direct `pandas-to-supabase` streaming without Parquet intermediation for daily syncs.
- **Level:** CRITICAL (Performance).

---

## 🛠️ Best Practices for Engineering Team
1. **Never Trust Relative Positions:** Always use a unique ID or absolute row index from `golden_schema.json`.
2. **Handle Errors Gracefully:** Cloud logging (Supabase) should be non-blocking. Use `try-except` for dependencies.
3. **Encryption First:** Never store raw financial data in plain text Parquet. Use the `security.py` module.
4. **Pure Logic in Provider:** Keep API quirks inside `providers/vietcap.py`, maintain a clean generic interface in `pipeline.py`.

---

*Refer to sub-project challenges for local issues:*
- [V2_CHALLENGES.md](file:///c:/Users/Admin/OneDrive/Learn%20Anything/Antigravity/1.Project%20Source/Version_2/V2_CHALLENGES.md)
- [V1_CHALLENGES.md](file:///c:/Users/Admin/OneDrive/Learn%20Anything/Antigravity/1.Project%20Source/Version_1/V1_CHALLENGES.md)
- [v4_challenges.md](file:///d:/Project_partial/Finsang/sub-projects/V4_Chart_Improve/v4_challenges.md)
- [v5_challenges.md](file:///c:/Users/Admin/OneDrive/Learn%20Anything/Antigravity/2.Project%20v2/sub-projects/V5_improdata/v5_challenges.md)
