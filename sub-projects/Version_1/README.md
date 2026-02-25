# Finsang Core: Version 1 (Legacy / Deprecated)

> [!WARNING]
> **DEPRECATED SUB-PROJECT**
> This directory contains the original Version 1 prototype of the Finsang Engine.
> It is maintained here strictly for historical reference and backward compatibility checks.

## Key Differences from Version 2 (Production)
- **Data Source:** Version 1 heavily relied on Fireant via Playwright and Unofficial API interception.
- **Mapping Logic:** Relied on `enumerate()` which caused severe *Index Drift* when the provider updated their payload items.
- **Storage:** Used raw unencrypted JSON/CSV data.

## Instruction for New Team Members
Do **NOT** use scripts from this directory for new feature development.
All active development, ETL execution, and data extraction must happen in `sub-projects/Version_2`.
