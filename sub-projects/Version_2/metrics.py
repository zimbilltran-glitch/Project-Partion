"""
Phase M — Metrics: Derived Ratios Engine
metrics.py — Calculates specialized dynamic financial ratios from Parquet sheets.

Calculates:
  - Gross Margin % (Biên lợi nhuận gộp) = QL_isa5 / QL_isa3 * 100
  - Net Margin %   (Biên lợi nhuận thuần) = QL_isa23 / QL_isa3 * 100
  - Current Ratio  (Hệ số T/T hiện hành) = CD_bsa1 / CD_bsa98
  - D/E Ratio      (Hệ số Nợ/Vốn CSH)     = CD_bsa97 / CD_bsa127

Usage:
  python Version_2/metrics.py --ticker VHC --period year
"""

import argparse
import pandas as pd
from pipeline import load_tab

def calc_metrics(ticker: str, period: str) -> pd.DataFrame:
    """
    Load CDKT and KQKD, calculate derived metrics for all periods,
    and return them as a DataFrame matching the load_tab format.
    """
    try:
        cdkt = load_tab(ticker, period, "cdkt")
        kqkd = load_tab(ticker, period, "kqkd")
    except Exception as e:
        print(f"  ❌ Cannot load parquet data: {e}")
        return pd.DataFrame()

    meta_cols = ["field_id", "vn_name", "unit", "level"]
    periods = [c for c in cdkt.columns if c not in meta_cols]

    # Helper for safe row extraction (returns pd.Series of 0s if missing)
    def get_row(df, fid):
        sub = df[df["field_id"] == fid]
        if sub.empty: return pd.Series(0.0, index=periods)
        return sub.iloc[0]

    # KQKD inputs
    rev   = get_row(kqkd, "kqkd_doanh_thu_thuan")   # Doanh thu thuần
    gross = get_row(kqkd, "kqkd_loi_nhuan_gop")     # Lợi nhuận gộp
    net   = get_row(kqkd, "kqkd_loi_nhuan_cua_co_dong_cua_cong_ty_me")  # LNST cổ đông cty mẹ

    # CDKT inputs
    ca    = get_row(cdkt, "cdkt_tai_san_ngan_han")   # Tài sản ngắn hạn
    cl    = get_row(cdkt, "cdkt_no_ngan_han")        # Nợ ngắn hạn
    debt  = get_row(cdkt, "cdkt_no_phai_tra")        # Nợ phải trả
    eq    = get_row(cdkt, "cdkt_von_chu_so_huu")     # Vốn chủ sở hữu

    rows = []

    # Helper to clean numeric values (safely parse strings, handle None)
    def clean_num(val):
        if val is None or val == "": return 0.0
        try: return float(val)
        except (ValueError, TypeError): return 0.0

    # 1. Gross Margin (%)
    gm_dict = {"field_id": "cstc1", "vn_name": "Biên lợi nhuận gộp", "unit": "%", "level": 1}
    for p in periods:
        v_rev = clean_num(rev[p])
        v_gross = clean_num(gross[p])
        gm_dict[p] = (v_gross / v_rev * 100) if v_rev != 0 else None
    rows.append(gm_dict)

    # 2. Net Margin (%)
    nm_dict = {"field_id": "cstc2", "vn_name": "Biên lợi nhuận thuần", "unit": "%", "level": 1}
    for p in periods:
        v_rev = clean_num(rev[p])
        v_net = clean_num(net[p])
        nm_dict[p] = (v_net / v_rev * 100) if v_rev != 0 else None
    rows.append(nm_dict)

    # 3. Current Ratio (x)
    cr_dict = {"field_id": "cstc3", "vn_name": "Hệ số T/T Hiện Hành", "unit": "lần", "level": 1}
    for p in periods:
        v_ca = clean_num(ca[p])
        v_cl = clean_num(cl[p])
        cr_dict[p] = (v_ca / v_cl) if v_cl != 0 else None
    rows.append(cr_dict)

    # 4. Debt/Equity Ratio (x)
    de_dict = {"field_id": "cstc4", "vn_name": "Hệ số Nợ/Vốn CSH", "unit": "lần", "level": 1}
    for p in periods:
        v_debt = clean_num(debt[p])
        v_eq   = clean_num(eq[p])
        de_dict[p] = (v_debt / v_eq) if v_eq != 0 else None
    rows.append(de_dict)

    # Construct dataframe using the ordered periods
    result_df = pd.DataFrame(rows)
    cols = ["field_id", "vn_name", "unit", "level"] + periods
    return result_df[cols]

def main():
    parser = argparse.ArgumentParser(description="Finsang V2.0 — Metrics Engine")
    parser.add_argument("--ticker", required=True, help="Stock ticker (e.g., VHC)")
    parser.add_argument("--period", choices=["year", "quarter"], default="year")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    print(f"\n{'═'*80}")
    print(f"  📈 METRICS ENGINE — {ticker} ({args.period.upper()})")
    print(f"{'═'*80}\n")

    df = calc_metrics(ticker, args.period)
    if df.empty:
        return

    # Print wide display
    periods = [c for c in df.columns if c not in ["field_id", "vn_name", "unit", "level"]]
    print_cols = ["Chỉ tiêu"] + periods[:5]  # View up to 5 most recent periods
    
    header = f"  {print_cols[0]:<25} | " + " | ".join([f"{c:>10}" for c in print_cols[1:]])
    print(header)
    print(f"  {'-'*80}")

    for _, row in df.iterrows():
        val_strs = []
        for p in print_cols[1:]:
            val = row[p]
            if val is None:
                val_strs.append(f"{'—':>10}")
            elif row["unit"] == "%":
                val_strs.append(f"{val:>9.1f}%")
            else:
                val_strs.append(f"{val:>10.2f}")
                
        line = f"  {row['vn_name']:<25} | " + " | ".join(val_strs)
        print(line)

    print(f"\n{'═'*80}\n")

if __name__ == "__main__":
    main()
