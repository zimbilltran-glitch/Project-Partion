"""
Phase V — Validate: CFO Financial Validation Engine
audit.py — Enforces strict accounting identities across all historical periods.

Rules (Task 3.3):
1. Total Assets = Total Liabilities + Total Equity (Tolerance: ±0.1%)
   bsa96 = bsa97 + bsa127
2. Total Assets = Current Assets + Non-Current Assets
   bsa96 = bsa1 + bsa45
3. Total Liabilities = Current Liabilities + Non-Current Liabilities
   bsa97 = bsa98 + bsa118

Usage:
  python Version_2/audit.py --ticker VHC --period year
"""

import argparse
from pathlib import Path
import pandas as pd

# Load pipeline context
from pipeline import load_tab

def run_checksums(df: pd.DataFrame) -> dict:
    """
    Given a wide DataFrame (from load_tab CDKT), run 3 primary checksums.
    Returns a dict mapping {period: {status: 'PASS'/'FAIL', details: dict}}
    """
    # Extract the period columns (drop metadata cols)
    meta_cols = ["field_id", "vn_name", "unit", "level"]
    periods = [c for c in df.columns if c not in meta_cols]

    # Helper to safely extract a row or return 0s if missing
    def get_row(fid: str):
        sub = df[df["field_id"] == fid]
        if sub.empty:
            return pd.Series(0.0, index=periods)
        return sub.iloc[0]

    # Map field_ids to rows safely
    row_A     = get_row("bsa96")   # TỔNG CỘNG TÀI SẢN
    row_CA    = get_row("bsa1")    # TÀI SẢN NGẮN HẠN
    row_NCA   = get_row("bsa45")   # TÀI SẢN DÀI HẠN
    
    row_L     = get_row("bsa97")   # NỢ PHẢI TRẢ
    row_CL    = get_row("bsa98")   # Nợ ngắn hạn
    row_NCL   = get_row("bsa118")  # Nợ dài hạn
    
    row_E     = get_row("bsa127")  # VỐN CHỦ SỞ HỮU

    results = {}
    tolerance = 0.001  # 0.1%

    for p in periods:
        A   = row_A[p] or 0.0
        CA  = row_CA[p] or 0.0
        NCA = row_NCA[p] or 0.0
        
        L   = row_L[p] or 0.0
        CL  = row_CL[p] or 0.0
        NCL = row_NCL[p] or 0.0
        
        E   = row_E[p] or 0.0

        # Check 1: A = L + E
        eq1_diff = abs(A - (L + E))
        eq1_pass = (eq1_diff / (A or 1)) <= tolerance

        # Check 2: A = CA + NCA
        eq2_diff = abs(A - (CA + NCA))
        eq2_pass = (eq2_diff / (A or 1)) <= tolerance

        # Check 3: L = CL + NCL
        eq3_diff = abs(L - (CL + NCL))
        eq3_pass = (eq3_diff / (L or 1)) <= tolerance

        is_pass = eq1_pass and eq2_pass and eq3_pass
        
        results[p] = {
            "status": "✅ PASS" if is_pass else "❌ FAIL",
            "A": A,
            "L_E": L + E,
            "eq1_pass": eq1_pass,
            "eq2_pass": eq2_pass,
            "eq3_pass": eq3_pass
        }

    return results

def main():
    parser = argparse.ArgumentParser(description="Finsang V2.0 — CFO Audit")
    parser.add_argument("--ticker", required=True, help="Stock ticker (e.g., VHC)")
    parser.add_argument("--period", choices=["year", "quarter"], default="year")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    print(f"\n{'═'*50}")
    print(f"  🏦 CFO AUDIT ENGINE — {ticker} ({args.period})")
    print(f"{'═'*50}\n")

    try:
        df = load_tab(ticker, args.period, "cdkt")
    except Exception as e:
        print(f"  ❌ Cannot load CDKT data for {ticker}: {e}")
        return

    results = run_checksums(df)

    # Print results
    print(f"  {'Period':<12} | {'Status':<8} | {'Assets':<12} | {'L + E':<12}")
    print(f"  {'-'*50}")
    
    passed = 0
    total = len(results)
    
    for p, res in sorted(results.items(), reverse=True):
        if "✅" in res["status"]: passed += 1
        
        A_str = f"{res['A']:,.0f}"
        LE_str = f"{res['L_E']:,.0f}"
        print(f"  {p:<12} | {res['status']:<8} | {A_str:>12} | {LE_str:>12}")
        
        if "❌" in res["status"]:
            print(f"    ⚠️ Failed items: Eq1(A=L+E):{res['eq1_pass']}, Eq2(A=CA+NCA):{res['eq2_pass']}, Eq3(L=CL+NCL):{res['eq3_pass']}")

    print(f"\n  📊 Summary: {passed}/{total} periods passed.")
    print(f"{'═'*50}\n")

if __name__ == "__main__":
    main()
