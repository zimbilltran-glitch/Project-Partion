# Simply Wall St v2.0 Design System

This document defines the design tokens and implementation guidelines for the Simply Wall St theme.

## 1. Color Palette

### Primary Context Colors
| Logic | HEX Code | CSS Variable | Use Case |
| :--- | :--- | :--- | :--- |
| **Checkmark Green**| `#26AE50` | `--s-success` | Valuation checklist passes |
| **Valuation Lime**| `#9ACA27` | `--s-valuation-lime` | Snowflake fill, Valuation highlights |
| **Failure Red** | `#E53935` | `--s-danger` | Valuation fail, Checklist alert |

### UI Surface Colors
| Layer | HEX Code | CSS Variable | Use Case |
| :--- | :--- | :--- | :--- |
| **Background** | `#1A1A1A` | `--s-bg-main` | Page body (Dark Mode) |
| **Sidebar BG** | `#262626` | `--s-bg-sidebar` | Navigation background |
| **Border** | `rgba(255,255,255,0.1)`| `--s-border` | Section dividers |
| **Text Solid** | `#FFFFFF` | `--s-text-primary`| Headings, Primary values |
| **Text Softer** | `#A0AEC0` | `--s-text-muted` | Labels, Auxiliary info |

## 2. Typography

- **Body Font Family:** `BureauSans, -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif`
- **Header Font Family:** `BureauSerif, ui-serif, Georgia, Cambria, "Times New Roman", Times, serif`
- **Headings:** `font-bold`, `tracking-tight`
- **Data Points:** `tabular-nums` for alignment in tables.
- **Sizes:**
  - `text-2xl` (24px): Page Headers
  - `text-lg` (18px): Section Titles
  - `text-sm` (14px): Body / Values
  - `text-xs` (12px): Labels / Captions

## 3. Component Styles

### Snowflake (Radar Chart)
- **Grid:** Hexagonal or Pentagonal
- **Fill:** `rgba(154, 202, 39, 0.2)` (Lime green `#9ACA27` with low opacity)
- **Stroke:** `#9ACA27` (2px thickness)

### Valuation Cards
- **Padding:** `p-4` or `1rem`
- **Border Radius:** `rounded-lg` (0.5rem)
- **Interactivity:** `hover:bg-gray-50`, `cursor-pointer`
- **Transition:** `transition-all duration-200`

### Navigation Sidebar
- **Width:** `240px`
- **Link State:** `active: border-l-4 border-primary`, `hover: text-primary`
- **Indicator:** Small circular badge for scores/counts.
