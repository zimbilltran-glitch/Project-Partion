# Research Findings: Simply Wall St Valuation Analysis

This document summarizes the technical and design findings from our research into the Simply Wall St valuation interface. It serves as a blueprint for the engineering and design team to begin implementation.

## 1. Design Language (V2.0)

### Visual Identity
- **Theme:** High-contrast Dark Mode.
- **Backgrounds:** Primary (`#1A1A1A`), Surface/Sidebar (`#262626`).
- **Accent Color (Valuation Lime):** `#9ACA27` — used extensively for the "Snowflake" gauge and high-value highlights.
- **Success/Failure:** Checkmark Green (`#26AE50`) and Alert Red (`#E53935`).

### Typography
The platform uses a sophisticated typography system to balance data density with legibility:
- **Body/Data:** `BureauSans` (fallback: `-apple-system`, `sans-serif`). Optimized for tabular numbers and labels.
- **Headings:** `BureauSerif` (fallback: `Georgia`, `serif`). Used for section headers to provide a professional, report-style aesthetic.

## 2. Key Components

### The Snowflake Chart (Radar Gauge)
- **Physics:** A 6-axis spider chart visualizing Value, Future, Past, Health, and Dividend.
- **Implementation:** Needs SVG overlay with a semi-transparent lime fill (`rgba(154, 202, 39, 0.2)`).

### Relative Valuation Bars
- **Behavior:** Horizontal bars comparing the target stock (e.g., MBB) against industry peers.
- **Logic:** The target stock is highlighted in **Valuation Lime** (`#9ACA27`), while peers are muted in `#4A5568`.

### Valuation Checklist
- **Interaction:** Collapsible rows with micro-animations.
- **Hover/Active:** Rows use a subtle highlight (`rgba(255, 255, 255, 0.08)`) to indicate interactivity.

---

## 3. Data Architecture (CFO View)

For the MBB (Banking) sector, the valuation relies on:
1. **DCF (Discounted Cash Flow):** Comparing Current Price vs. Estimated Future Cash Flows.
2. **Relative Metrics:** Price-to-Earnings (PE) vs. Industry Peers and Market Averages.
3. **Score Calculation:** A 6-point checklist determining the "Valuation Score" (e.g., 5/6).
