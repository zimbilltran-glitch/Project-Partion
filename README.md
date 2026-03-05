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

## 🏗️ Directory Hierarchy

```text
Finsang/
├── frontend/             # Primary React + Vite visualization (OLED Dark)
├── sub-projects/         # High-level engine components
│   ├── Version_2/        # Core ETL Pipeline (Vietcap API -> Supabase)
│   ├── Version_1/        # [DEPRECATED] Legacy / Baseline code
│   ├── PDF_TRANS_Pipeline/ # Financial PDF extraction suite (Phase 6)
│   ├── V3_SimplyWallSt/  # Simply Wall St 360 Overview Integration (Done)
│   ├── V4_Chart_Improve/ # Analysis Charts (Recharts Integration - Done)
│   └── V5_improdata/     # Performance Tuning & Data Integrity (Done)
├── internal-skills/      # Agent capabilities & Automated test suites
├── design-themes/        # UI/UX reference systems (Simply Wall St, Fireant)
└── data/                 # (Gitignored) Encrypted financial store
```

---

## 🚦 Status: Phase 7.0 Production Readiness (ACTIVE)
Dự án đã hoàn tất các giai đoạn tối ưu hóa hiệu năng (Phase 5.5) và bổ sung Metrics chuyên ngành Ngân hàng/Chứng khoán (Phase 5.6). Toàn bộ 30 mã VN30 đã được resync với độ chính xác tuyệt đối (Ground Truth Mapping). Hệ thống đã được rà soát bảo mật (RLS Hardening) và fix lỗi requests timeout. Frontend đã sẵn sàng cho Production Deploy.

*— Developed by the Finsang Engineering Team under CTO Supervision.*
