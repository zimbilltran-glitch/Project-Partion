# 📝 V4 Changelog — Analysis Charts Integration

## [2026-03-03]
### Added
- Integrated **Recharts** library for interactive data visualization.
- Created `AnalysisTab.jsx` as a container for sector-specific financial charts.
- Implemented Recharts Wrappers:
  - `CompareBarChart.jsx`
  - `TrendLineChart.jsx`
  - `StackedAreaChart.jsx`
  - `DualAxisChart.jsx`
- Added `chartMappings.js` to define sector-specific (`bank`, `sec`, `normal`) data mappings between Supabase items and chart series.
- Added Bank-specific metrics to `metrics.py`: CASA, COF, YOEA, NPL, CIR.

### Improved
- **UI Aesthetics**:
  - Concise chart titles (uppercase, letter-spaced).
  - Reduced font sizes for axes labels and legends (10px) for a premium look.
  - Custom dark-mode tooltips with Glassmorphism effects.
  - Optimized chart margins and container heights.
- **Performance**:
  - Fixed Hook order violation in `AnalysisTab.jsx` by lifting data transformations to the top level.
  - Optimized data loading with `useAnalysisChartsData` hook.
- **Data Access**: Updated Supabase RLS policies and table permissions to ensure seamless data fetching for charts.

### Fixed
- Resolved React Hook crash when switching between different sectors (VHC, TCB, SSI).
- Fixed data key mapping for bank TOI growth.
