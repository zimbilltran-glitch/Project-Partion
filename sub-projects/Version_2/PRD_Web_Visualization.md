# Product Requirements Document (PRD): Finsang V2 Web Visualization (Refined)

## 1. Executive Summary
**Purpose**: Replace the legacy Version 1 visualization with a professional, Vietcap-inspired web dashboard powered by the Version 2 B.L.A.S.T pipeline.

#### Components:
- **Problem Statement**: Version 1 data is inconsistent and lacks the structural integrity of Version 2. Local V2 data is inaccessible to the web UI.
- **Proposed Solution**: Implement a professional ETL/Sync pipeline to overwrite legacy Supabase tables with high-fidelity V2 data. Redesign the frontend using professional UI/UX standards to mimic the Vietcap IQ experience.
- **Strategic Roles**: 
    - **Data Operations**: `@data-engineer`, `@data-scientist`, and `@data-engineering-data-pipeline` oversee the "One Big Table" transformation and quality assurance.
    - **Visual Excellence**: `@ui-ux-designer` and `@ui-ux-pro-max` handle the dashboard skinning, typography, and interactive components.
- **Success Metrics**: 
    - Successful deletion of all V1 legacy data.
    - 100% parity between Terminal Viewer and Web UI.
    - "Wow" factor UI following Vietcap design tokens.

---

## 2. Problem Definition
- **Legacy Cleanup**: Old data in Supabase is prone to errors and mapping failures.
- **Structure Gap**: V1 frontend expects a specific "Wide" format that V2 must provide natively.

---

## 3. Solution Overview

#### 3.1 Data Foundation (V2 Root)
Version 2's `golden_schema.json` and `metrics.py` serve as the absolute source of truth for all calculations and row hierarchies.

#### 3.2 UI/UX Optimization (Vietcap Style)
- Replicate Vietcap IQ's tabbed navigation.
- Use professional color palettes (FinTech Dark/Light modes) from `@ui-ux-pro-max`.
- Implement responsive, accessible tables with mini-trend charts.

---

## 4. Operational Requirements

| Role | Responsibility |
|---|---|
| `@data-engineer` | Design the Supabase table schema for high-performance wide-table reads. |
| `@data-engineering-data-pipeline` | Orchestrate the Sync sequence: Decrypt -> Pivot -> Upsert. |
| `@data-scientist` | Validate that all derived metrics (margins, growth rates) remain accurate post-sync. |
| `@ui-ux-designer` | Create a design system inspired by Vietcap, focusing on information density and clarity. |
| `@ui-ux-pro-max` | Provide optimal font pairings and chart configurations for financial data. |

---

## 5. Scope & Constraints
- **In-Scope**: Cleanup of old Supabase data, direct overwrite of existing tables, V2-based visualization.
- **Out-of-Scope**: Future predictive modeling (AI).

---

## 9. Implementation Phases (Step-by-Step)

| Phase | Milestone | Description |
|-----------|--------------|-------------|
| **Phase 1: Purge** | Legacy Deletion | Clear all rows from `balance_sheet_wide`, etc. |
| **Phase 2: Bridge** | Sync Engine | Develop `sync_supabase.py` using V2 logic. |
| **Phase 3: Populate** | Data Load | Batch upsert V2 data (VHC, FPT...) to clean tables. |
| **Phase 4: Skin** | UI Redesign | Apply Vietcap styling via `@ui-ux-pro-max`. |
| **Phase 5: Audit** | CTO Review | Final verification of data and UI polish. |
