"""
Phase S — Stylize: Terminal Tab Viewer
viewer.py — Mimics Vietcap IQ's BCTC tab interface in the terminal.

Usage:
    python Version_2/viewer.py --ticker VHC --sheet kqkd --period year
    python Version_2/viewer.py --ticker VHC --sheet cdkt --period quarter --n 8
    python Version_2/viewer.py --ticker VHC --sheet lctt --period year
    python Version_2/viewer.py --ticker VHC --sheet note --period quarter

Sheets:  cdkt | kqkd | lctt | note
Periods: year | quarter
"""

import argparse, sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from pipeline import load_tab
from metrics import calc_metrics
from audit import run_checksums

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box
from rich.panel import Panel
from rich.columns import Columns
from rich.style import Style

console = Console()

# ─── Config ───────────────────────────────────────────────────────────────────
SHEET_LABELS = {
    "cdkt": "Bảng Cân Đối Kế Toán",
    "kqkd": "Kết Quả Kinh Doanh",
    "lctt": "Lưu Chuyển Tiền Tệ",
    "note": "Thuyết Minh / Bổ Sung",
    "cstc": "Chỉ Số Tài Chính",
}
PERIOD_LABELS = {
    "year":    "Năm",
    "quarter": "Quý",
}

LEVEL_STYLES = {
    0: Style(bold=True, color="bright_white"),
    1: Style(bold=True, color="cyan"),
    2: Style(color="white"),
    3: Style(color="bright_black"),
    4: Style(color="bright_black", italic=True),
    5: Style(color="bright_black", italic=True),
}

HEADER_STYLE = Style(bold=True, color="green")
POS_STYLE    = Style(color="bright_white")
NEG_STYLE    = Style(color="red")
NULL_STYLE   = Style(color="bright_black")

INDENT_CHARS = ["", "  ", "    ", "      ", "        ", "          "]


def fmt_value(val, unit: str) -> Text:
    """Format a numeric value with thousand separators."""
    if val is None:
        return Text("—", style=NULL_STYLE)
    try:
        fval = float(val)
    except (TypeError, ValueError):
        return Text("—", style=NULL_STYLE)

    if unit in ("%", "lần"):
        formatted = f"{fval:,.2f}"
    elif unit == "đồng/cp":
        formatted = f"{fval:,.0f}"
    else:
        # Convert VND to tỷ đồng (billions): raw values are in VND (đồng)
        billions = fval / 1_000_000_000_000  # 1 tỷ = 1e12 VND ??? check scale
        # Actually Vietcap API returns values already in VND (not billions)
        # Let's display in tỷ đồng (divide by 1e9)
        if abs(fval) >= 1e9:
            billions = fval / 1e9
            formatted = f"{billions:,.1f}"
        elif abs(fval) >= 1e6:
            millions = fval / 1e6
            formatted = f"{millions:,.2f}M"
        elif fval == 0.0:
            formatted = "—"
        else:
            formatted = f"{fval:,.0f}"

    if fval < 0:
        return Text(formatted, style=NEG_STYLE)
    elif fval == 0:
        return Text("—", style=NULL_STYLE)
    return Text(formatted, style=POS_STYLE)


def render_header(ticker: str, sheet: str, period: str, n_cols: int, audit_results: dict):
    """Render the top banner mimicking Vietcap IQ."""
    sheet_name  = SHEET_LABELS.get(sheet, sheet.upper())
    period_name = PERIOD_LABELS.get(period, period)

    # Tab bar
    sheets = ["cdkt", "kqkd", "lctt", "note", "cstc"]
    tab_parts = []
    for s in sheets:
        label = SHEET_LABELS[s]
        if s == sheet:
            tab_parts.append(f"[bold green on dark_green] {label} [/]")
        else:
            tab_parts.append(f"[dim] {label} [/]")
    tabs = "  ".join(tab_parts)

    # Period toggle
    periods = ["year", "quarter"]
    toggle_parts = []
    for p in periods:
        lbl = PERIOD_LABELS[p]
        if p == period:
            toggle_parts.append(f"[bold cyan]【{lbl}】[/]")
        else:
            toggle_parts.append(f"[dim]{lbl}[/]")
    toggle = "  ".join(toggle_parts)

    console.print()
    console.rule(f"[bold green]🦁 FINSANG V2.0  ·  {ticker.upper()}  ·  Báo Cáo Tài Chính[/]")
    console.print(f"\n  {tabs}\n")
    
    # Audit badge (only for standard sheets, not derived metrics)
    audit_badge = ""
    if audit_results and sheet != "cstc":
        # Check if the most recent period passed
        latest_period = list(audit_results.keys())[0] if audit_results else None
        if latest_period:
            status = audit_results[latest_period]["status"]
            # To avoid Rich MarkupError with nested brackets, use this simple format
            audit_badge = rf"   \[CFO Audit: {status}]"

    console.print(f"  Hiển thị: {toggle}   [dim]({n_cols} kỳ gần nhất)[/]{audit_badge}\n")


def build_table(df, sheet: str, period: str, n_cols: int) -> Table:
    """Build the rich Table from a pivoted DataFrame."""
    period_cols = [c for c in df.columns if c not in ("field_id", "vn_name", "unit", "level")]
    # Take n most recent periods (already sorted newest→oldest by load_tab)
    shown_cols = period_cols[:n_cols]

    unit_label = "tỷ đồng"

    table = Table(
        box=box.MINIMAL_DOUBLE_HEAD,
        show_header=True,
        header_style="bold green",
        show_lines=False,
        padding=(0, 1),
        expand=True,
    )

    # Columns
    table.add_column(f"Chỉ tiêu  [{unit_label}]", style="", min_width=38, no_wrap=False)
    for col in shown_cols:
        table.add_column(col, justify="right", min_width=10, no_wrap=True)

    # Rows
    for _, row in df.iterrows():
        level   = int(row.get("level", 0))
        label   = row["vn_name"]
        unit    = row.get("unit", "")
        indent  = INDENT_CHARS[min(level, 5)]
        lbl_sty = LEVEL_STYLES.get(level, LEVEL_STYLES[2])

        # Label cell
        lbl_text = Text(indent + label, style=lbl_sty)

        # Value cells
        val_cells = [fmt_value(row.get(c), unit) for c in shown_cols]

        table.add_row(lbl_text, *val_cells)

    return table


def main():
    parser = argparse.ArgumentParser(description="Finsang Terminal Viewer")
    parser.add_argument("--ticker",  default="VHC",     help="Stock ticker")
    parser.add_argument("--sheet",   default="kqkd",    choices=["cdkt","kqkd","lctt","note","cstc"])
    parser.add_argument("--period",  default="year",    choices=["year","quarter"])
    parser.add_argument("--n",       type=int, default=8, help="Number of periods to show")
    args = parser.parse_args()

    try:
        if args.sheet == "cstc":
            df = calc_metrics(args.ticker, args.period)
            if df.empty: raise FileNotFoundError("Metrics payload empty.")
        else:
            df = load_tab(args.ticker, args.period, args.sheet)
    except FileNotFoundError as e:
        console.print(f"\n[red]❌ {e}[/]")
        console.print("[yellow]Hint: Run pipeline first:[/]  python Version_2/pipeline.py --ticker VHC\n")
        sys.exit(1)

    # Run CFO Audit quietly for header badge
    audit_results = {}
    try:
        cdkt_df = load_tab(args.ticker, args.period, "cdkt")
        audit_results = run_checksums(cdkt_df)
    except Exception:
        pass

    period_cols = [c for c in df.columns if c not in ("field_id","vn_name","unit","level")]
    n_cols = min(args.n, len(period_cols))

    render_header(args.ticker, args.sheet, args.period, n_cols, audit_results)
    table = build_table(df, args.sheet, args.period, n_cols)
    console.print(table)

    # Footer
    console.print(f"\n  [dim]Nguồn: Vietcap IQ  ·  Đơn vị: tỷ đồng  ·  {len(df)} chỉ tiêu  ·  {n_cols} kỳ hiển thị[/]\n")
    console.rule(style="dim")


if __name__ == "__main__":
    main()
