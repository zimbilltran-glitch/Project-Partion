# Technical Challenges: Replicating Simply Wall St

Implementing the Simply Wall St aesthetic and valuation logic involves several technical hurdles that the team needs to address.

## 1. Design Replication Challenges

### Proprietary Typography
- **Issue:** Simply Wall St uses custom fonts (`BureauSans` and `BureauSerif`).
- **Solution:** We must use high-quality fallbacks like **Inter** for body and **EB Garamond** or **Georgia** for headers to maintain the "premium" feel.

### The "Snowflake" Gauge
- **Complexity:** The chart isn't a static image; it's a dynamic data visualization.
- **Challenge:** Replicating the specific curvature and "organic" feel of the 6-axis chart using standard libraries (like Recharts or Chart.js) may require custom SVG paths.

### Dark Mode Contrast
- **Challenge:** Maintaining WCAG accessibility standards (4.5:1 ratio) on a `#1A1A1A` background while using bright lime and red accents requires careful opacity management.

---

## 2. Data Engineering Challenges

### DCF Logic Gap
- **Issue:** The public page displays the *result* (e.g., "41.7% Undervalued") but doesn't expose the full DCF spreadsheet (WACC, Terminal Growth, etc.).
- **Challenge:** Our backend must reverse-engineer or implement its own DCF calculation engine using `vnstock` data to justify the "Fair Value" display.

### Peer Dynamic Logic
- **Challenge:** Peer groups (VCB, TCB, etc.) are dynamic based on the stock being viewed. We need a robust "Similar Company" lookup service to populate the Relative Valuation component accurately.

---

## 3. Frontend Performance

### Micro-interactivity
- **Challenge:** Simply Wall St uses a lot of hover-triggered reveals and transitions. We need to ensure these animations are hardware-accelerated (using `transform` and `opacity`) to prevent jank, especially on mobile devices.
