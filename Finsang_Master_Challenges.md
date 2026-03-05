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

### 6. Synchronous Pipeline & Huge Schema Bottlenecks (V5) - ✅ SOLVED
- **Symptom:** `v5_full_resync.py` taking 45+ minutes to run 30 tickers. RAM/CPU spike.
- **Root Cause:** `subprocess.run` overhead. Huge 1MB schema files loaded repeatedly.
- **Solution:** 
  1. Created **`lite_schema.json`** (<200KB) for bot processing.
  2. Refactored resync script to use **`ThreadPoolExecutor`** (parallel threads).
  3. Optimized **Stream-to-DB** flow (skip redundant disk I/O).
- **Impact:** VN30 resync reduced from **45 mins** to **~28 seconds**.
- **Level:** CRITICAL (Performance).

### 7. Bank Note API 403 Forbidden (CASA Limitation)
- **Symptom:** Cannot calculate CASA (Demand Deposits) for Banks.
- **Root Cause:** Vietcap API for `section=NOTE` returns `HTTP 403 Forbidden` for most bank tickers on the web integration endpoint.
- **Solution:** Documented as a **Limitation**. CASA is currently bypassed. User must manually verify this through official PDF reports via `PDF_TRANS_Pipeline`.
- **Level:** MEDIUM.

---

### 8. Import Chain Blocking & Singleton DB client ✅ RESOLVED
- **Symptom**: Pipeline bị treo (hanging) hoặc crash khi import `security.py` hoặc tạo hàng loạt `SupabaseClient`.
- **Root Cause**: Phụ thuộc chéo (Circular import) và pool connection của Supabase bị cạn kiệt trong vòng lặp ThreadPool.
- **Solution**: 
  - Tách logic Supabase Client thành `sb_client.py` (Singleton).
  - Viết `run_metrics_batch.py` độc lập để handle import chain sạch.
- **Level**: MEDIUM.

### 9. CSTC Tab Data Erosion (The "Strip" Bug) ✅ RESOLVED
- **Symptom**: Tab CSTC chỉ hiện 7 dòng indicators thay vì 40+ dòng như thiết kế.
- **Root Cause**: `calculate_cstc.py` (legacy) xóa sạch bảng ratios và chỉ insert 7 dòng.
- **Solution**: 
  - Deprecate `calculate_cstc.py`.
  - Thay thế bằng `run_metrics_batch.py` gọi engine `metrics.py` (full 40+ metrics).
- **Level**: HIGH.

---

### 10. Cash Flow Identity Gap (BL-3) ✅ RESOLVED
- **Symptom**: Cash flow equations `Net CF = Op + Inv + Fin` were not balancing across all sectors (FPT, MBB, KDH). MBB had completely missing data.
- **Root Cause**: Incorrect mapping of `vietcap_key` in `lite_schema.json`. Normal sector operating cash flow was mapped to a sub-field (`cfa20` instead of `cfa36`), and Bank sector mappings were absent or incorrect.
- **Solution**: 
  - Probed the raw API JSON output directly via python scripts.
  - Remapped keys based on empirically verified identity equations (`cfa36` for Normal Op, `cfb57/cfb76/cfb77/cfb79` for Banks).
  - Ensured correct sector logic (`cdkt_bank_tong_tai_san`) in `cfo_audit_bl2_bl3.py`.
- **Level**: HIGH.

---

## 🛠️ Best Practices for Engineering Team
1. **Never Trust Relative Positions:** Always use a unique ID or absolute row index from `golden_schema.json`.
2. **Handle Errors Gracefully:** Cloud logging should be non-blocking. Use `try-except` for dependencies.
3. **Encryption First:** Never store raw financial data in plain text Parquet. Use the `security.py` module.
4. **Pure Logic in Provider:** Keep API quirks inside `providers/vietcap.py`, maintain a clean generic interface in `pipeline.py`.
5. **Singleton for External Services:** Always use a shared client (like `sb_client.py`) for DB connections to prevent pooling exhaustion.

---

## 🔗 Project Footnotes
- [Finsang Master Team Guide](Finsang_Master_Team_Guide.md)
- [Finsang Master Active Roadmap](Finsang_Master_Active_Roadmap.md)
- [v5_challenges.md](sub-projects/V5_improdata/v5_challenges.md)

