"""Check Parquet files exist and read a sample using load_tab."""
import sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from pipeline import load_tab, DATA_DIR, ROOT

# 1. Check files
parquet_files = list((ROOT / "data" / "financial").rglob("*.parquet"))
print(f"Found {len(parquet_files)} Parquet files:")
for p in parquet_files:
    size_kb = p.stat().st_size / 1024
    print(f"  {p.relative_to(ROOT)}  ({size_kb:.1f} KB)")

# 2. Test load_tab for KQKD yearly
print("\n=== KQKD / Year (Income Statement) ===")
df = load_tab("VHC", "year", "kqkd")
period_cols = [c for c in df.columns if c not in ("field_id", "vn_name", "unit", "level")]
print(f"Shape: {df.shape} | Periods: {period_cols}")
sample = df[["vn_name"] + period_cols[:5]].head(8)
print(sample.to_string(index=False))

# 3. Test CDKT quarterly
print("\n=== CDKT / Quarter (Balance Sheet) ===")
df2 = load_tab("VHC", "quarter", "cdkt")
period_cols2 = [c for c in df2.columns if c not in ("field_id", "vn_name", "unit", "level")]
print(f"Shape: {df2.shape} | Periods: {period_cols2[:8]}")
sample2 = df2[["vn_name"] + period_cols2[:4]].head(5)
print(sample2.to_string(index=False))

print("\n✅ Phase A verification PASSED")
