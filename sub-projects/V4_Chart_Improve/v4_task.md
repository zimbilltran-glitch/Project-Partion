# 📋 V4 Task Tracker — Analysis Charts Integration

> **Thư mục Project**: `sub-projects/V4_Chart_Improve`
> **Kế hoạch**: `v4_implementation_plan.md`
> **Trạng thái**: � Đang triển khai (Phase 1-3 ✅ | Phase 4 đang chạy)

---

## ✅ Phase 1: Blueprint & Layer (Setup & Data Routing)
- [x] **P1.0**: Tạo môi trường V4 (`v4_implementation_plan.md`, `v4_task.md`, `v4_changelog.md`...)
- [x] **P1.1**: Cài đặt dependency `recharts` vào `frontend/package.json`.
- [x] **P1.2**: Update `App.jsx` cấu hình Tab mới có `id: 'ANALYSIS_CHARTS'`.
- [x] **P1.3**: Xây dựng thư viện transform data `frontend/src/hooks/useAnalysisChartsData.js` lấy data Supabase đang có trên context.
- [x] **P1.4**: Tạo file mapping chỉ số `frontend/src/utils/chartMappings.js`.

## 🧩 Phase 2: Assemble (Frontend Components)
- [x] **P2.1**: Dựng `AnalysisTab.jsx` (Container). Lọc & truyền data theo nhóm ngành (Bank, Sec, Normal).
- [x] **P2.2**: Dựng Recharts Wrapper: `CompareBarChart.jsx`
- [x] **P2.3**: Dựng Recharts Wrapper: `TrendLineChart.jsx`
- [x] **P2.4**: Dựng Recharts Wrapper: `StackedAreaChart.jsx`
- [x] **P2.5**: Dựng Recharts Wrapper: `DualAxisChart.jsx`
- [/] **P2.6**: Connect toàn bộ Chart vào `AnalysisTab.jsx` với Data tương ứng.
  - [x] Core charts (Perf, Growth, Assets).
  - [x] Bank specific (NPL, CASA/COF).
  - [x] Sec specific (Revenue structure).
  - [ ] Normal specific (Cash Flow, Profit structure).
  - [ ] Bank specific (Income structure, Risk buffer).

## 🎨 Phase 3: Style (Theme & Polish)
- [x] **P3.1**: Style Grid CSS cho Tab (Desktop 2 columns, Mobile 1 column).
- [x] **P3.2**: Custom Recharts Tooltip giống SWS Theme (Dark glass, Inter font).
- [x] **P3.3**: Hoàn thiện Formatter numbers trục Y và Tooltip.
- [x] **P3.4**: Tinh chỉnh UI (Tiêu đề viết gọn, font chữ nhỏ 10px).

## 🧪 Phase 4: Test (Audit & Finalize)
- [/] **P4.1**: CFO Audit: Verify data chart với số bảng / Excel Sheet. (VHC, TCB, SSI verified).
- [x] **P4.2**: CTO Audit: Optimize React re-render & Hook order fix.
- [ ] **P4.3**: Release & Update Changelog.
