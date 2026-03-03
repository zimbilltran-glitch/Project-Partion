"""Output viewer.py results as plain text for verification (no ANSI codes)."""
import sys, warnings, io
warnings.filterwarnings("ignore")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from pipeline import load_tab
from rich.console import Console

OUT_DIR = Path(__file__).parent

def run_view(ticker, sheet, period, n=8):
    from viewer import build_table, SHEET_LABELS, PERIOD_LABELS

    # Create a plain-text console (no ANSI)
    buf = io.StringIO()
    c = Console(file=buf, no_color=True, width=120)

    c.print(f"\n{'='*80}")
    c.print(f"  📊 {ticker} | {SHEET_LABELS[sheet]} | {PERIOD_LABELS[period]} | {n} kỳ")
    c.print(f"{'='*80}\n")

    df = load_tab(ticker, period, sheet)
    table = build_table(df, sheet, period, n)
    c.print(table)

    period_cols = [c2 for c2 in df.columns if c2 not in ("field_id","vn_name","unit","level")]
    c.print(f"\n  Chỉ tiêu: {len(df)} | Kỳ hiển thị: {min(n,len(period_cols))} | Tất cả kỳ: {period_cols}\n")
    return buf.getvalue()

results = []
for sheet, period in [("kqkd","year"), ("cdkt","quarter"), ("lctt","year"), ("note","year")]:
    results.append(run_view("VHC", sheet, period, n=8))

out_f = OUT_DIR / "_viewer_output.txt"
out_f.write_text("\n".join(results), encoding="utf-8")
print(f"Written to {out_f}  ({out_f.stat().st_size} bytes)")
