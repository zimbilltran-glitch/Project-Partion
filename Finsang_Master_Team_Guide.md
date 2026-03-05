# Finsang Team Onboarding & Engineering Guide

This document is the primary reference for all engineering contributors to the Finsang project. It defines our standards, workflows, and technical foundations.

---

## 🏗️ Project Architecture Map

The project is strictly organized into functional groups to ensure long-term maintainability:

- **`/frontend`**: The production React + Vite visualization layer (Phase 2.0-7.0).
    - Uses OLED Dark aesthetics.
    - Connects to Supabase for near real-time financial data.
- **`/sub-projects`**: High-level feature integrations and core engines (CORE ONLY).
    - `Version_2/`: Core "Finsang Engine" (`pipeline.py`, `security.py`, `metrics.py`). Cleaned of explorations.
    - `V5_improdata/`: **Performance Engine**. Contains ops scripts (`run_metrics_batch.py`) and schema builders.
- **`/archive_legacy`**: **CRITICAL FOR AGENTS.** This directory contains 60+ archived scripts and audit data moved during the v5.1.5 cleanup. If a script is missing from `/sub-projects`, check here.
    - `explorations/`: Deprecated research, debug, and probe scripts.
    - `clutter_cleanup/`: Raw logs, Excel pilot files, and temporary audit reports.
- **`data/`**: (Gitignored/Untracked) Local encrypted Parquet backups.
- **`internal-skills/`** & **`design-themes/`**: Supporting resources.

---

## 🛠️ Onboarding Instructions

### 1. Environment Synchronization
You MUST maintain two `.env` files. Do not commit these to Git.

**Root `.env` (Pipeline/Sync):**
```bash
SUPABASE_URL="yours"
SUPABASE_KEY="yours (service_role for writes)"
FINSANG_ENCRYPTION_KEY="generated-via-security-init"
```

**Frontend `.env` (in /frontend):**
```bash
VITE_SUPABASE_URL="yours"
VITE_SUPABASE_ANON_KEY="yours (anon for reads)"
```

### 2. High-Performance ETL Workflow (Phase 5+)
Every data refresh MUST follow the [QUARTERLY_UPDATE_GUIDE.md](QUARTERLY_UPDATE_GUIDE.md):
1.  **Sync:** `python sub-projects/Version_2/v5_full_resync.py` (Parallel resync to Supabase).
2.  **Metrics:** `python sub-projects/V5_improdata/run_metrics_batch.py` (CSTC calculation).

---

## 📝 Coding & Contribution Standards

### 🛡️ Data Integrity Rules
- **Absolute Mapping Only:** Never use relative iteration (`idx`, `enumerate`) for mapping API keys.
- **Exact Ground Truth Mapping:** Vietcap API keys (`isa1, bsa1`) are layout rows. Only map keys verified against audited statements.
- **Lite Schema First:** Use `lite_schema.json` for high-speed processing to avoid overhead of the 1MB `golden_schema.json`.

### 🛡️ Security Standards
- **RLS Enabled:** All tables must have Row Level Security enabled. `anon` is restricted to SELECT only.
- **Requests Timeout:** ALWAYS use `timeout=10` in `requests.get/post` to prevent DoS.

### 🌿 Git & Workflow
- **Commit Messages:** Use: `[UI]`, `[ETL]`, `[SEC]`, `[LOG]`, `[DOC]`.
- **Merge Requirement:** All code must pass a `@cto-mentor-supervisor` audit check.

---

## 🚦 Troubleshooting

| Problem | Solution |
|---|---|
| "Parquet data shows as gibberish" | Verify your `FINSANG_ENCRYPTION_KEY` matches original storage key. |
| "Supabase sync fails (403/401)" | Ensure `SUPABASE_KEY` is the `service_role` key for write access. |
| "Metrics are NaN" | Check if the ticker has the correct sector mapping in `sector.py`. |

---

*Maintainer: Finsang Engineering Lead / @cto-mentor-supervisor*
