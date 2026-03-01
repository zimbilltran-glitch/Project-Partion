# Finsang Version Control & Update Timeline

Traceable history of system updates, version tags, and feature deployments.

---

## 🚀 Version History

### [v2.3.0-audit] — 2026-03-01 (Current)
- **Audit:** Full project review — 10 findings documented → `findings.md`
- **Task Restructuring:** New 6-phase task plan (v3.0) — sector-aware frontend, dynamic routing, metrics per sector
- **Key findings:** F-001 (crash bug), F-003 (frontend sector-blind), F-004 (hardcoded sectors), F-005 (RLS disabled)
- **Confirmed:** Supabase đã có đầy đủ 31 VN30 tickers data (source: vietcap)

### [v2.2.0] — 2026-02-28
- **Feature:** VN30 data enrichment via `vn30_enrichment.py` — 31 tickers synced to Supabase.
- **Fix:** "0.0% Mapped" bug — sequential index vs absolute row mapping.
- **UI:** Removed `<MiniBarChart />`, added Autocomplete search.

### [v2.1.0] — 2026-02-26
- **Feature:** Hierarchical Table UI (Vietcap Style) refinement in React/Vite.
- **Fix:** Corrected index mapping bug for FPT and other tickers in `pipeline.py`.
- **Audit:** Full project documentation rename and folder restructuring.
- **Docs:** Implementation of `Finsang_Master_Logs.md`, `Finsang_Master_Challenges.md`, and `Finsang_Team_Guide.md`.

### [v2.0.0] — 2026-02-25
- **Feature:** React Web Dashboard with OLED Dark Theme.
- **Feature:** Supabase Cloud Sync pipeline.
- **Security:** Implementation of Fernet encryption for Parquet storage.
- **Architecture:** Migration from relative indexing to Golden Schema absolute mapping.

### [v1.0.0] — 2026-02-21
- **Feature:** Initial extraction pipeline (Vietcap API).
- **Feature:** Terminal UI Viewer (Rich).
- **Architecture:** Basic provider pattern implementation.

---

## 📦 Component Status

| Component | Version | Health | Last Update | Notes |
|---|---|---|---|---|
| ETL Pipeline | 2.0.1 | 🟢 Stable | 2026-02-28 | Sector routing implemented |
| Golden Schema | 2.2.0 | 🟢 Stable | 2026-02-28 | 946 fields, 10 sector-specific sheets |
| Supabase Sync | 2.0.0 | 🟡 Bug | 2026-02-28 | `load_tab_from_supabase()` crash (F-001) |
| React Frontend | 2.1.0-dev | 🔴 Blocked | 2026-02-28 | Sector-blind (F-003) |
| Metrics Engine | 2.0.0 | 🟡 Partial | 2026-02-28 | 3 sector calcs exist, not shown on web |
| Supabase Data | 2.2.0 | 🟢 Full | 2026-02-28 | 31 VN30 tickers, 206K+ rows |
| Security (RLS) | — | 🔴 Disabled | 2026-02-28 | Must enable before deploy (F-005) |
| Fireant Pipeline | 1.0.0 | 🟡 Standalone | 2026-02-23 | Exists in tools/, not integrated V2 |

---

## 🗺️ Active Roadmap

| # | Phase | Status | Target |
|---|---|---|---|
| 1 | 🔧 Critical Fixes (F-001, F-002, F-005) | ⏳ Next | Week 1 |
| 2 | 🏦 Sector Intelligence (dynamic routing) | ⏳ Pending | Week 1-2 |
| 3 | 🖥️ Frontend Sector-Aware | ⏳ Pending | Week 2-3 |
| 4 | 📊 Metrics per Sector | ⏳ Pending | Week 3-4 |
| 5 | 🔍 Data Validation & Cross-ref | ⏳ Pending | Week 4 |
| 6 | 🚀 Polish & Deploy | ⏳ Pending | Week 5 |

*Full details → `task_plan.md` v3.0*

---

## 📎 Key Documents

| Doc | Purpose |
|---|---|
| `task_plan.md` | Active task plan v3.0 — 6 phases |
| `findings.md` | Audit findings F-001 → F-010 |
| `Finsang_Master_Logs.md` | Historical audit trail |
| `Finsang_Master_Challenges.md` | Verified engineering solutions |
| `Finsang_Team_Guide.md` | Onboarding & standards |
