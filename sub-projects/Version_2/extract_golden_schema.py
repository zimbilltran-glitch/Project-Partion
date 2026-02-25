"""
Phase B — Blueprint: Golden Schema Extractor v2
@skill: financial-data-normalizer
Confirmed sheet structure from VHC_BCTC.xlsx probe:
  - 'Balance Sheet'      → CDKT  (128 rows, footer at rows 122+)
  - 'Income Statement'   → KQKD  (31 rows,  footer at rows 25+)
  - 'Cash Flow'          → LCTT  (47 rows,  footer at rows 41+)
  - 'Note'               → NOTE  (163 rows, footer at rows 157+)
Data rows: from Excel row index 11 onward (0-indexed via pandas: row 10 = year header)
Period type row  : index 9  → ['Năm', 'Quý']
Period value row : index 10 → [2018, 2019, ..., 2025, Q1/2022, ...]
"""

import json
import re
from pathlib import Path
import pandas as pd
import numpy as np

ROOT     = Path(__file__).parent.parent
XLSX     = ROOT / "VHC_BCTC.xlsx"
OUT_DIR  = Path(__file__).parent
PROBE_TMP = OUT_DIR / "_probe.txt"

# --- Sheet registry -----------------------------------------------------------
SHEET_REGISTRY = {
    "Balance Sheet":    {"sheet_id": "CDKT", "vn_name": "Cân Đối Kế Toán",         "en_name": "Balance Sheet",       "footer_start": 122},
    "Income Statement": {"sheet_id": "KQKD", "vn_name": "Kết Quả Kinh Doanh",      "en_name": "Income Statement",    "footer_start": 25},
    "Cash Flow":        {"sheet_id": "LCTT", "vn_name": "Lưu Chuyển Tiền Tệ",      "en_name": "Cash Flow Statement", "footer_start": 41},
    "Note":             {"sheet_id": "NOTE", "vn_name": "Thuyết Minh / Bổ Sung",   "en_name": "Notes / Supplements", "footer_start": 157},
}

# Rows (0-indexed from start of sheet) where data begins and header sits
YEAR_HEADER_ROW = 10   # row 10  = year values (2018, 2019…)
DATA_START_ROW  = 11   # row 11+ = actual financial line items

FOOTER_KEYWORDS = {
    "Liên Hệ", "CÔNG TY CỔ PHẦN CHỨNG KHOÁN VIETCAP",
    "Địa chỉ:", "Website:", "Email:", "Điện thoại:"
}

UNIT_DEFAULT = "tỷ đồng"

def is_footer(label: str) -> bool:
    return any(kw in label for kw in FOOTER_KEYWORDS)

def detect_unit(label: str) -> str:
    lo = label.lower()
    if any(k in lo for k in [" %", "tỷ lệ", "tỷ suất", "biên", "roe", "roa", "ros", "p/e", "p/b"]):
        return "%"
    if "lần" in lo:
        return "lần"
    if "cổ phiếu" in lo or "eps" in lo:
        return "đồng/cp"
    if "triệu đồng" in lo:
        return "triệu đồng"
    return UNIT_DEFAULT

def infer_dtype(label: str) -> str:
    lo = label.lower()
    if any(k in lo for k in ["%", "tỷ lệ", "lần", "p/e", "p/b", "roe", "roa"]):
        return "DECIMAL(12,4)"
    if any(k in lo for k in ["eps", "lãi cơ bản", "lãi trên cổ phiếu"]):
        return "DECIMAL(14,2)"
    return "DECIMAL(22,2)"

def slugify(text: str) -> str:
    """Convert Vietnamese label to safe ASCII field_id via NFD decomposition."""
    import unicodedata
    text = str(text).strip().lower()
    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace("đ", "d").replace("Đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s_]", "", text)
    text = re.sub(r"\s+", "_", text.strip())
    text = re.sub(r"_+", "_", text)
    return text[:55]

def parse_periods(df: pd.DataFrame):
    """Extract column headers: returns list of (col_index, period_type, period_label)."""
    period_type_row = df.iloc[9].tolist()   # 'Năm' or 'Quý'
    period_val_row  = df.iloc[10].tolist()  # 2018.0, 2019.0 … or 'Q1/2022'

    periods = []
    current_type = None
    for col_i, (ptype, pval) in enumerate(zip(period_type_row, period_val_row)):
        if pd.notna(ptype) and str(ptype).strip() in ("Năm", "Quý"):
            current_type = str(ptype).strip()
        if col_i == 0:
            continue  # label column
        if pd.isna(pval):
            continue
        val_str = str(pval)
        # Year: e.g. 2018.0 → '2018'
        if re.match(r"^\d{4}\.0$", val_str):
            label = val_str.replace(".0", "")
            ptype_label = "year"
        elif re.match(r"^\d{4}$", val_str):
            label = val_str
            ptype_label = "year"
        # Quarter: could be 'Q1/2022' string or float/int representing quarter step
        elif "/" in val_str:
            label = val_str.strip()
            ptype_label = "quarter"
        else:
            label = val_str
            ptype_label = current_type.lower() if current_type else "year"
        periods.append((col_i, ptype_label, label))
    return periods

def parse_sheet(xl: pd.ExcelFile, sheet_name: str, meta: dict) -> tuple[list[dict], list[str]]:
    df = xl.parse(sheet_name, header=None)
    periods    = parse_periods(df)
    sheet_id   = meta["sheet_id"]
    footer_idx = meta["footer_start"]

    fields   = []
    seen_ids = {}

    data_rows = df.iloc[DATA_START_ROW:].reset_index(drop=True)

    for i, row in data_rows.iterrows():
        if i >= footer_idx:
            break
        raw_label = row.iloc[0]
        if pd.isna(raw_label):
            continue
        label = str(raw_label).strip()
        if not label or is_footer(label):
            continue

        # Detect indent level from leading whitespace
        raw_str  = str(raw_label)
        indent   = len(raw_str) - len(raw_str.lstrip(" \xa0"))
        level    = min(indent // 2, 5)

        # Build field_id
        slug    = slugify(label)
        base_id = f"{sheet_id.lower()}_{slug}"
        if base_id in seen_ids:
            seen_ids[base_id] += 1
            field_id = f"{base_id}_{seen_ids[base_id]}"
        else:
            seen_ids[base_id] = 0
            field_id = base_id

        # Extract period values for this row
        period_values = {}
        for col_i, ptype, plabel in periods:
            if col_i < len(row):
                v = row.iloc[col_i]
                period_values[f"{ptype}:{plabel}"] = None if (pd.isna(v) or v == "") else float(v)

        fields.append({
            "field_id":        field_id,
            "sheet":           sheet_id,
            "sheet_en":        meta["en_name"],
            "sheet_vn":        meta["vn_name"],
            "vn_name":         label,
            "en_name":         "",
            "unit":            detect_unit(label),
            "data_type":       infer_dtype(label),
            "level":           level,
            "row_number":      DATA_START_ROW + i,
            "vietcap_mapped":  False,
            "sample_values":   period_values,
            "notes":           ""
        })

    period_labels = [f"{ptype}:{plabel}" for _, ptype, plabel in periods]
    return fields, period_labels


def main():
    print(f"\n📂 Opening: {XLSX}")
    xl = pd.ExcelFile(XLSX)
    print(f"📋 Sheets: {xl.sheet_names}\n")

    all_fields  = []
    sheet_stats = {}
    all_periods = {}

    for sheet_name, meta in SHEET_REGISTRY.items():
        if sheet_name not in xl.sheet_names:
            print(f"  ⚠️  Sheet '{sheet_name}' not found in workbook — skipping")
            continue
        fields, period_labels = parse_sheet(xl, sheet_name, meta)
        all_fields.extend(fields)
        sheet_stats[meta["sheet_id"]] = len(fields)
        all_periods[meta["sheet_id"]] = period_labels
        print(f"  ✅ {meta['sheet_id']} ({sheet_name}): {len(fields)} fields, {len(period_labels)} periods")

    # ── golden_schema.json ──────────────────────────────────────────────────
    schema_path = OUT_DIR / "golden_schema.json"
    schema_out = {
        "version":       "2.0",
        "source_file":   "VHC_BCTC.xlsx",
        "generated_at":  "2026-02-24T22:40:57+07:00",
        "auditor":       "@financial-data-normalizer + @cto-mentor-supervisor",
        "total_fields":  len(all_fields),
        "sheet_counts":  sheet_stats,
        "period_columns": all_periods,
        "fields":        all_fields,
    }
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema_out, f, ensure_ascii=False, indent=2)
    print(f"\n✅ golden_schema.json → {schema_path}  ({len(all_fields)} total fields)")

    # ── schema_report.md ────────────────────────────────────────────────────
    report_path = OUT_DIR / "schema_report.md"
    lines = [
        "# Golden Schema Report — Phase B Output",
        "",
        "> **Source:** `VHC_BCTC.xlsx` | **Ticker:** VHC | **Date:** 2026-02-24",
        "> **Generated by:** `@financial-data-normalizer`",
        "> **CTO Review:** `@cto-mentor-supervisor` (sign-off pending)",
        "",
        "## Sheet Summary",
        "",
        "| Sheet ID | Excel Tab | VN Name | Fields |",
        "|---|---|---|---|",
    ]
    for sheet_name, meta in SHEET_REGISTRY.items():
        sid = meta["sheet_id"]
        cnt = sheet_stats.get(sid, 0)
        lines.append(f"| `{sid}` | {sheet_name} | {meta['vn_name']} | **{cnt}** |")

    lines += [
        f"| **TOTAL** | | | **{len(all_fields)}** |",
        "",
        "## Period Columns Detected",
        "",
        "| Sheet | Years Available | Quarters Available |",
        "|---|---|---|",
    ]
    for sid, periods in all_periods.items():
        yrs = [p.split(":")[1] for p in periods if p.startswith("year:")]
        qts = [p.split(":")[1] for p in periods if p.startswith("quarter:")]
        lines.append(f"| `{sid}` | {', '.join(yrs[:10])} | {', '.join(qts[:8]) or '—'} |")

    lines += [""]

    for sheet_name, meta in SHEET_REGISTRY.items():
        sid = meta["sheet_id"]
        sheet_fields = [f for f in all_fields if f["sheet"] == sid]
        if not sheet_fields:
            continue
        lines.append(f"## {sid} — {meta['en_name']}")
        lines.append("")
        lines.append("| # | field_id | vn_name | unit | dtype | lvl |")
        lines.append("|---|---|---|---|---|---|")
        for i, f in enumerate(sheet_fields):
            indent = "　" * f["level"]
            lines.append(
                f"| {i+1} | `{f['field_id']}` | {indent}{f['vn_name']} | {f['unit']} | `{f['data_type']}` | {f['level']} |"
            )
        lines.append("")

    lines += [
        "---",
        "",
        "## 🏛️ CTO Phase B Gate Checklist",
        "",
        "- [ ] All 4 sheets parsed without errors",
        "- [ ] `field_id` uniqueness confirmed",
        "- [ ] Period columns (Year + Quarter) detected correctly",
        "- [ ] `golden_schema.json` written to `Version_2/`",
        "- [ ] Extraction strategy decision documented in `findings.md`",
        "- [ ] Phase B Gate: PM sign-off received",
        "",
        "> **CTO Note:** *(to be filled after review)*",
        "> **CTO Score:** —/100",
        "> **Timestamp:** 2026-02-24T22:40:57+07:00",
        "> **Auditor:** `@cto-mentor-supervisor`",
    ]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ schema_report.md → {report_path}")

    # Clean up temp probe files
    for tmp in [OUT_DIR / "_probe.txt", OUT_DIR / "_probe2.txt"]:
        if tmp.exists():
            tmp.unlink()
            print(f"🗑️  Deleted temp: {tmp.name}")

    print(f"\n{'═'*55}")
    print(f"  Phase B Blueprint — COMPLETE")
    print(f"  Total fields registered: {len(all_fields)}")
    for sid, cnt in sheet_stats.items():
        print(f"    {sid}: {cnt} fields")
    print(f"{'═'*55}\n")

if __name__ == "__main__":
    main()
