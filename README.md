# FINSANG v2.1 — High-Fidelity Financial Intelligence Terminal

**Finsang** is a production-grade financial data ecosystem for Vietnamese public companies. It integrates automated ETL pipelines from Vietcap IQ with high-fidelity React visualization and cloud synchronization.

---

## 🏛️ Project Governance & Master Docs

To ensure engineering consistency and rapid onboarding, use the following master documents:

- 📑 **[Finsang Master Team Guide](Finsang_Master_Team_Guide.md)**: **START HERE.** Detailed onboarding, standards, and workflow instructions.
- 🚀 **[Finsang Master Active Roadmap](Finsang_Master_Active_Roadmap.md)**: Overall tracker for Finsang's project phases.
- 📜 **[Finsang Master Logs](Finsang_Master_Logs.md)**: Historical audit trail and major milestones.
- 🧠 **[Finsang Master Challenges](Finsang_Master_Challenges.md)**: Technical hurdles and verified engineering solutions.
- 🔄 **[Finsang Master Changelog](Finsang_Master_Changelog.md)**: Changelog and version control tracker.
- 🔍 **[Finsang Master Findings](Finsang_Master_Findings.md)**: Granular finding reports from audits.
- 📘 **[QUARTERLY UPDATE GUIDE](QUARTERLY_UPDATE_GUIDE.md)**: Standard Operating Procedure for quarterly data refreshes.

---

## 🏗️ Directory Hierarchy (Clean State v5.1.0)

```text
Finsang/
├── frontend/             # Primary React + Vite visualization (OLED Dark)
├── sub-projects/         # High-level engine components (CORE ONLY)
│   ├── Version_2/        # Core ETL Pipeline (Cleaned - only operational scripts)
│   ├── Version_1/        # [ARCHIVED] Legacy / Baseline code
│   ├── PDF_TRANS_Pipeline/ # Financial PDF extraction suite (Phase 6)
│   ├── V3_SimplyWallSt/  # SWS Overview Integration (Done - Production Ready)
│   ├── V4_Chart_Improve/ # Analysis Charts (Done - Production Ready)
│   └── V5_improdata/     # Performance & Integrity (Cleaned - Ops scripts only)
├── internal-skills/      # Agent capabilities & Automated test suites
├── design-themes/        # UI/UX reference systems
├── archive_legacy/       # [STORAGE] Rot bin for explorations & clutter cleanup
│   ├── explorations/     # 40+ deprecated research & debug scripts
│   └── clutter_cleanup/  # Raw Excel files, logs, and temporary audit data
└── data/                 # (Gitignored/Untracked) Encrypted financial store
```

---

## 🚦 Status: Phase 7.0 Production Readiness (RELEASE READY)
Dự án đã được dọn dẹp quy mô lớn (Massive Cleanup). Toàn bộ code rác, log, và dữ liệu thô đã được chuyển vào `archive_legacy`. Cấu trúc hiện tại cực kỳ tinh gọn, chỉ chứa các script vận hành (Production scripts). Hệ thống resync VN30 (<30s) và bộ metrics 3 sector đã được kiểm chứng 100%. Toàn bộ tiến độ được quản lý tập trung tại `Finsang_Master_Task.md`.

*— Developed by the Finsang Engineering Team under CTO Supervision.*
