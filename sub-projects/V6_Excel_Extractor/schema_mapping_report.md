# V6 Schema Mapping & Ground Truth Audit Report

> **Last Updated:** 2026-03-07
> **Status:** Phase 6.6 Active
> **Total Keys Mapped:** 257

## 📊 Mapping Summary (Phase 6.6)
We successfully expanded the `golden_schema.json` coverage across all sectors by using a hybrid approach (Fuzzy Matching + Manual Overrides).

| Sector | Report | Keys Mapped | Status |
|---|---|---|---|
| **BANK** | Balance Sheet | 61 | ✅ SUCCESS |
| **BANK** | Cash Flow | 37 | ✅ SUCCESS |
| **SEC** | Balance Sheet | 121 | ✅ SUCCESS |
| **NORMAL** | Balance Sheet | 122 | ✅ SUCCESS |

**Techniques Used:**
1. **Financial Synonym Dictionary:** Normalizing `TSCĐ` -> `Tài sản cố định`, `CTCK` -> `Công ty chứng khoán`.
2. **Vietnamese Accent Removal:** Used `remove_accents` to improve fuzzy reliability.
3. **Manual Overrides:** Hardcoded mappings for high-priority rows (e.g., Total Assets `bsb96`).
4. **Supabase Dictionary:** Upserted all 257 mappings to `api_translation_dictionary`.

---

## 🔍 Ground Truth Audit (Validation)
Results from `verify_ground_truth.py` comparing Supabase data (Frontend) vs. Physical Excel files.

### 1. MBB (Ngân hàng) - [77.1% Accuracy]
- **Matches:** 54/70
- **Drift:** 15 fields
- **Note:** Missing key "Tổng tài sản" was fixed via `MANUAL_OVERRIDES`. Minor drifts remain in sub-categories due to specific bank accounting templates.

### 2. SSI (Chứng khoán) - [68.3% Accuracy]
- **Matches:** 95/139
- **Drift:** 44 fields
- **Issue:** Securities reports have many custom rows that need tighter mapping in `golden_schema.json`.

### 3. FPT (Phi tài chính) - [10.7% Accuracy] ⚠️
- **Matches:** 13/122
- **Issue:** **Excel Row Offset Drift (F-023)**.
- **Cause:** The current `sync_supabase.py` relies on `row_number` from `golden_schema.json`. However, FPT's actual row layout in Excel differs from the VHC-based template in the schema.
- **Fix Required:** Change sync logic to map by `vietcap_key` (API ID) instead of absolute row index.

---

## 📔 Note Sheet Integration (F-024)
Successfully bypassed API 403 Forbidden for financial notes.

- **Data Source:** Sheet "Note" extracted directly from 12 Excel files.
- **DB Sink:** Created `note` table on Supabase.
- **Record Count:** ~120,000 cells.
- **Frontend:** New "Thuyết minh" tab added to `App.jsx`, verified working on local host.

---
**Next Action:** Refactor `sync_supabase.py` to use `vietcap_key` for data extraction to solve the 10.7% FPT drift.
