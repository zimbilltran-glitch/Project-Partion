"""
V3 Phase P1.2 — Fetch Company Overview
=======================================
Fetch thị trường (P/E, P/B, ROE, ROA, D/E, EPS, market cap, v.v.)
cho tất cả VN30 tickers từ vnstock company.ratio_summary(),
rồi upsert vào Supabase table `company_overview`.

Source:  vnstock (VCI source) → company.ratio_summary()
Fields:  pe, pb, roe, roa, de, eps, bvps, ev, dividend_yield,
         net_profit_margin, gross_margin, current_ratio
DB:      Supabase `company_overview` (upsert on ticker)

Usage:
    python fetch_company_overview.py              # All VN30
    python fetch_company_overview.py --ticker VHC # One ticker
    python fetch_company_overview.py --dry-run    # No DB write
"""

import os
import sys
import time
import argparse
from datetime import date
from pathlib import Path

# ── .env load ─────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / ".env")
except ImportError:
    pass

# ── Add Version_2 to path ─────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Version_2"))
from sector import get_all_tickers, get_sector

RATE_DELAY = 1.0   # seconds between tickers (vnstock rate limit)

# ── Sector labels ─────────────────────────────────────────────────────────────
SECTOR_LABEL = {
    "bank":   "Ngân hàng",
    "sec":    "Chứng khoán",
    "normal": "Phi tài chính",
}

# ── Fetch from vnstock ─────────────────────────────────────────────────────────
def fetch_company_overview(ticker: str) -> dict | None:
    """
    Fetch ratio_summary + company overview from vnstock (VCI source).
    Returns a dict ready for Supabase upsert, or None on failure.
    """
    try:
        from vnstock import Vnstock
    except ImportError:
        raise ImportError("Run: pip install vnstock")

    sector = get_sector(ticker)

    # ── ratio_summary: full valuation + profitability snapshot ────────────────
    rs_row = None
    for source in ["VCI", "TCBS"]:
        try:
            s = Vnstock().stock(symbol=ticker, source=source)
            rs = s.company.ratio_summary()
            if rs is not None and len(rs) > 0:
                rs_row = rs.iloc[0].to_dict()
                break
        except Exception:
            continue

    if rs_row is None:
        return None

    def _f(key, fallback=None):
        """Safe float extract from ratio_summary row."""
        v = rs_row.get(key)
        if v is None:
            return fallback
        try:
            f = float(v)
            return None if (f != f) else round(f, 6)  # NaN check
        except (TypeError, ValueError):
            return fallback

    # ── Market cap: ev (enterprise value) is in VND, use issue_share * close ─
    # ev is already available, market cap = ev from vnstock context
    issue_share = _f("issue_share")
    charter_cap = _f("charter_capital")

    # EPS and price: bvps (book value per share in VND), eps in VND
    pe   = _f("pe")
    pb   = _f("pb")
    eps  = _f("eps")
    bvps = _f("bvps")

    # Infer current price from P/E × EPS (approximate)
    current_price = None
    if pe and eps and pe > 0 and eps > 0:
        current_price = round(pe * eps, 0)

    # Market cap in billions VND
    market_cap_b = None
    if issue_share and current_price:
        market_cap_b = round((issue_share * current_price) / 1_000_000_000, 1)
    elif _f("ev"):
        market_cap_b = round(_f("ev") / 1_000_000_000, 1)

    # Dividend yield: vnstock returns as ratio (0.03 = 3%)
    div_yield = _f("dividend")
    if div_yield is not None:
        div_yield = round(div_yield * 100, 2)  # Convert to %

    # Revenue growth (%), net profit growth (%)
    rev_growth = _f("revenue_growth")
    np_growth  = _f("net_profit_growth")
    if rev_growth is not None:
        rev_growth = round(rev_growth * 100, 2)
    if np_growth is not None:
        np_growth = round(np_growth * 100, 2)

    return {
        "ticker":            ticker.upper(),
        "sector":            sector,
        "industry":          SECTOR_LABEL.get(sector, "Phi tài chính"),
        # Valuation
        "pe_ratio":          pe,
        "pb_ratio":          pb,
        "ps_ratio":          _f("ps"),
        "ev_ebitda":         _f("ev_per_ebitda"),
        # Profitability
        "eps":               round(eps, 2) if eps else None,
        "bvps":              round(bvps, 2) if bvps else None,
        "roe":               _f("roe"),
        "roa":               _f("roa"),
        "roic":              _f("roic"),
        "net_profit_margin": _f("net_profit_margin"),
        "gross_margin":      _f("gross_margin"),
        "ebit_margin":       _f("ebit_margin"),
        # Growth
        "revenue_growth_pct":  rev_growth,
        "np_growth_pct":       np_growth,
        # Liquidity
        "current_ratio":     _f("current_ratio"),
        "quick_ratio":       _f("quick_ratio"),
        "cash_ratio":        _f("cash_ratio"),
        "interest_coverage": _f("interest_coverage"),
        # Leverage
        "de_ratio":          _f("de"),          # D/E
        "le_ratio":          _f("le"),          # Financial leverage
        # Market
        "market_cap":        market_cap_b,      # Tỷ VND
        "ev":                round(_f("ev") / 1_000_000_000, 1) if _f("ev") else None,
        "issue_share":       int(issue_share) if issue_share else None,
        "dividend_yield":    div_yield,
        "ebitda":            round(_f("ebitda") / 1_000_000_000, 1) if _f("ebitda") else None,
        # Score placeholders — filled by calc_snowflake.py
        "score_value":       None,
        "score_future":      None,
        "score_past":        None,
        "score_health":      None,
        "score_dividend":    None,
        "current_price":     current_price,
        "updated_at":        date.today().isoformat(),
    }


# All known columns in company_overview (post-migration)
OVERVIEW_COLS = {
    "ticker", "sector", "industry", "pe_ratio", "pb_ratio", "ps_ratio",
    "ev_ebitda", "eps", "bvps", "roe", "roa", "roic", "net_profit_margin",
    "gross_margin", "ebit_margin", "revenue_growth_pct", "np_growth_pct",
    "current_ratio", "quick_ratio", "cash_ratio", "interest_coverage",
    "de_ratio", "le_ratio", "market_cap", "ev", "issue_share",
    "dividend_yield", "ebitda", "score_value", "score_future", "score_past",
    "score_health", "score_dividend", "current_price", "updated_at",
}

def upsert_overview(row: dict, dry_run: bool = False) -> bool:
    if dry_run:
        print(f"    [DRY RUN] Would upsert: {list(row.keys())[:8]}...")
        return True

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL / SUPABASE_KEY missing from .env")

    from supabase import create_client
    sb = create_client(url, key)
    # Only keep known columns + non-None values
    clean = {k: v for k, v in row.items() if v is not None and k in OVERVIEW_COLS}
    sb.table("company_overview").upsert(clean, on_conflict="ticker").execute()
    return True



# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="V3 P1.2 — Fetch Company Overview → Supabase"
    )
    parser.add_argument("--ticker",  help="Single ticker (default: all VN30)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tickers = [args.ticker.upper()] if args.ticker else get_all_tickers(vn30_only=True)
    mode = "DRY RUN" if args.dry_run else "WRITE TO SUPABASE"

    print(f"\n{'='*60}")
    print(f"  Finsang V3 — Company Overview Fetcher (P1.2)")
    print(f"  Tickers: {len(tickers)} | Mode: {mode}")
    print(f"  Source:  vnstock VCI -> company.ratio_summary()")
    print(f"{'='*60}\n")

    ok, failed = 0, []

    for i, ticker in enumerate(tickers, 1):
        print(f"  [{i:>2}/{len(tickers)}] {ticker} ... ", end="", flush=True)
        try:
            row = fetch_company_overview(ticker)
            if row is None:
                print("[SKIP] No data returned")
                failed.append(ticker)
                continue

            pe_str  = f"P/E={row['pe_ratio']:.1f}" if row.get("pe_ratio") else "P/E=--"
            pb_str  = f"P/B={row['pb_ratio']:.2f}" if row.get("pb_ratio") else "P/B=--"
            roe_str = f"ROE={row['roe']*100:.1f}%" if row.get("roe") else "ROE=--"
            upsert_overview(row, dry_run=args.dry_run)
            print(f"[OK]  {pe_str}  {pb_str}  {roe_str}")
            ok += 1
        except Exception as e:
            print(f"[FAIL] {e}")
            failed.append(ticker)

        if i < len(tickers):
            time.sleep(RATE_DELAY)

    print(f"\n{'='*60}")
    print(f"  [OK] {ok} tickers | [FAIL] {len(failed)} failed")
    if failed:
        print(f"  Failed: {', '.join(failed)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
