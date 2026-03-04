# Finsang Team Onboarding & Engineering Guide

This document is the primary reference for all engineering contributors to the Finsang project. It defines our standards, workflows, and technical foundations.

---

## 🏗️ Project Architecture Map

The project is strictly organized into functional groups to ensure long-term maintainability:

- **`/frontend`**: The production React + Vite visualization layer.
    - Uses Tailwind (if applicable) and Vanilla CSS for OLED Dark aesthetics.
    - Connects to Supabase for near real-time financial data.
- **`/sub-projects`**: High-level feature integrations and core engines.
    - `Version_2/`: The core "Finsang Engine" (API extraction orchestrator `pipeline.py`, AES-128 `security.py`, and CFA-grade `metrics.py`).
    - `V3_SimplyWallSt/`: The 360 Overview feature integration.
    - `V4_Chart_Improve/`: Analysis Charts feature using Recharts library.
    - `V5_improdata/`: Data Integrity refactoring, Exact Ground Truth Schema builder, and Performance tuning scripts.
- **`/internal-skills`**: Agent-specific capabilities and automated testing suites.
- **`/design-themes`**: Curated UI/UX reference systems (Simply Wall St, Fireant styles).
- **`/docs`**: Granular finding reports and historical challenges.

---

## 🛠️ Onboarding Instructions

### 1. Environment Synchronization
You MUST maintain two `.env` files. Do not commit these to Git.

**Root `.env` (Pipeline):**
```bash
SUPABASE_URL="yours"
SUPABASE_KEY="yours"
FINSANG_ENCRYPTION_KEY="generated-via-security-init"
```

**Frontend `.env`:**
```bash
VITE_SUPABASE_URL="yours"
VITE_SUPABASE_ANON_KEY="yours"
```

### 2. The B.L.A.S.T Workflow
Every feature delivery MUST follow these steps:
1.  **[B]lueprint:** Update `golden_schema.json` if adding new financial rows.
2.  **[L]ink:** Verify the API provider in `providers/`.
3.  **[A]rchitect:** Test Parquet generation in local `data/`.
4.  **[S]tylize:** Update the React UI to match pixel-perfection.
5.  **[T]rigger:** Run the Supabase sync and verify cloud logs.

---

## 📝 Coding & Contribution Standards

### 🛡️ Data Integrity Rules
- **Absolute Mapping Only:** Never use relative iteration (`idx`, `enumerate`) for mapping API keys.
- **No Positional Guesses:** Vietcap API keys (`isa1, bsa1`) are sequential layout rows, NOT semantic identifiers. Only map keys that have been verified via **Exact Ground Truth Mapping** against audited public statements.
- **Encryption by Default:** Never use `pd.to_parquet()` directly. Always use the `security.py` wrapper to ensure data is encrypted at rest.

### 🌿 Git & Workflow
- **Branch Naming:** `feature/ui-refinement`, `fix/index-drift`, `audit/q4-validation`.
- **Commit Messages:** Use descriptive prefixes: `[UI]`, `[ETL]`, `[SEC]`, `[DOC]`.
- **Merge Requirement:** All code must pass a `@cto-mentor-supervisor` audit check before merging to `main`.

---

## 🚦 Troubleshooting

| Problem | Solution |
|---|---|
| "Parquet data shows as gibberish" | Verify your `FINSANG_ENCRYPTION_KEY` matches the one used during storage. |
| "Supabase sync fails" | Check for IP rate limits and ensure your `service_role` key has bypass RLS permission. |
| "UI doesn't show new quarters" | Ensure the pipeline run was triggered with `--period quarter` and synced. |

---

*Maintainer: Finsang Engineering Lead / @cto-mentor-supervisor*
