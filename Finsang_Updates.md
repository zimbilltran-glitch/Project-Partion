# Finsang Version Control & Update Timeline

Traceable history of system updates, version tags, and feature deployments.

---

## 🚀 Version History

### [v2.1.0] — 2026-02-26 (In Progress)
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

| Component | Version | Health | Last Update |
|---|---|---|---|
| ETL Pipeline | 2.0.1 | 🟢 Stable | 2026-02-25 |
| Terminal UI | 2.0.0 | 🟢 Stable | 2026-02-24 |
| React Frontend | 2.1.0-dev | 🟡 Refining | 2026-02-26 |
| Streamlit Backup | 1.0.0 | 🟢 Stable | 2026-02-25 |
| Supabase Sync | 1.1.0 | 🟢 Stable | 2026-02-25 |

---

## 🛠️ Deployment Roadmap
- [x] Local Parquet storage (encrypted)
- [x] Supabase Cloud integration (data sync)
- [ ] Automated CI/CD (GitHub Actions)
- [ ] Production hosting for React Dashboard
- [ ] Multi-ticker batch processing optimization
