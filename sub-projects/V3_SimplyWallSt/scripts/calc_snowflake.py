"""
V3 Phase P1.4 — Snowflake Score Calculator
===========================================
5-dimension scoring inspired by Simply Wall St methodology,
adapted for VN market (VN30 companies).

Dimensions (each 0.0 – 5.0):
  VALUE:    Valuation attractiveness   (P/E, P/B, EV/EBITDA vs sector)
  FUTURE:   Growth prospects           (revenue/NP growth, ROE trend)
  PAST:     Historical performance     (ROE, ROA, ROIC, net_profit_margin)
  HEALTH:   Financial health           (current_ratio, D/E, interest_coverage)
  DIVIDEND: Income attractiveness      (dividend_yield, payout stability)

Scoring: rule-based thresholds calibrated for VN30 universe.
Scores are written to `company_overview` table (score_* columns).

Usage:
    python calc_snowflake.py              # All tickers that have company_overview
    python calc_snowflake.py --ticker VHC
    python calc_snowflake.py --dry-run
"""

import os
import sys
import argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / ".env")
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Version_2"))
from sector import get_all_tickers, get_sector


# ── Sector P/E benchmarks (VN30 calibrated) ───────────────────────────────────
PE_BENCH   = {"bank": 10.0, "sec": 12.0, "normal": 14.0}
PB_BENCH   = {"bank":  1.5, "sec":  2.0, "normal":  2.5}
ROE_GOOD   = {"bank": 0.12, "sec": 0.15, "normal": 0.15}
ROE_GREAT  = {"bank": 0.18, "sec": 0.20, "normal": 0.20}


def _clamp(v: float, lo: float = 0.0, hi: float = 5.0) -> float:
    return max(lo, min(hi, v))


def _safe(d: dict, key: str) -> float | None:
    v = d.get(key)
    if v is None:
        return None
    try:
        f = float(v)
        return None if f != f else f   # NaN check
    except (TypeError, ValueError):
        return None


# ── 1. VALUE score ─────────────────────────────────────────────────────────────
def score_value(row: dict, sector: str) -> float:
    """
    Score 0–5 based on valuation multiples vs sector benchmarks.
    Lower P/E + P/B = more attractive.
    """
    pe   = _safe(row, "pe_ratio")
    pb   = _safe(row, "pb_ratio")
    evebi = _safe(row, "ev_ebitda")
    bench_pe = PE_BENCH.get(sector, 14.0)
    bench_pb = PB_BENCH.get(sector, 2.5)

    pts = 0.0
    n   = 0

    # P/E scoring (max 2 pts)
    if pe and pe > 0:
        ratio = pe / bench_pe
        if   ratio < 0.6:  pts += 2.0
        elif ratio < 0.8:  pts += 1.5
        elif ratio < 1.0:  pts += 1.0
        elif ratio < 1.3:  pts += 0.5
        else:              pts += 0.0
        n += 1

    # P/B scoring (max 1.5 pts)
    if pb and pb > 0:
        ratio = pb / bench_pb
        if   ratio < 0.5:  pts += 1.5
        elif ratio < 0.8:  pts += 1.0
        elif ratio < 1.0:  pts += 0.7
        elif ratio < 1.5:  pts += 0.3
        else:              pts += 0.0
        n += 1

    # EV/EBITDA scoring (max 1.5 pts)
    if evebi and evebi > 0:
        if   evebi < 6:   pts += 1.5
        elif evebi < 9:   pts += 1.0
        elif evebi < 12:  pts += 0.5
        else:             pts += 0.0
        n += 1

    if n == 0:
        return 2.5   # Neutral when no data
    # Scale to 5
    max_pts = 2.0 + (1.5 if pb else 0) + (1.5 if evebi else 0)
    return _clamp((pts / max_pts) * 5.0) if max_pts > 0 else 2.5


# ── 2. FUTURE score ────────────────────────────────────────────────────────────
def score_future(row: dict, sector: str) -> float:
    """
    Score 0–5 based on growth indicators.
    """
    rev_g = _safe(row, "revenue_growth_pct")   # % e.g. 12.5 = 12.5%
    np_g  = _safe(row, "np_growth_pct")
    roe   = _safe(row, "roe")

    pts = 0.0
    n   = 0

    # Revenue growth (max 1.5 pts)
    if rev_g is not None:
        if   rev_g > 20:   pts += 1.5
        elif rev_g > 10:   pts += 1.2
        elif rev_g > 5:    pts += 0.8
        elif rev_g > 0:    pts += 0.4
        else:              pts += 0.0
        n += 1

    # Net profit growth (max 2 pts)
    if np_g is not None:
        if   np_g > 25:    pts += 2.0
        elif np_g > 15:    pts += 1.5
        elif np_g > 5:     pts += 1.0
        elif np_g > 0:     pts += 0.5
        else:              pts += 0.0
        n += 1

    # ROE trend proxy (max 1.5 pts)
    if roe is not None:
        good = ROE_GOOD.get(sector, 0.15)
        gret = ROE_GREAT.get(sector, 0.20)
        if   roe > gret:   pts += 1.5
        elif roe > good:   pts += 1.0
        elif roe > 0:      pts += 0.5
        else:              pts += 0.0
        n += 1

    if n == 0:
        return 2.5
    max_pts = (1.5 if rev_g is not None else 0) + \
              (2.0 if np_g  is not None else 0) + \
              (1.5 if roe   is not None else 0)
    return _clamp((pts / max_pts) * 5.0) if max_pts > 0 else 2.5


# ── 3. PAST score ──────────────────────────────────────────────────────────────
def score_past(row: dict, sector: str) -> float:
    """
    Score 0–5 based on historical profitability track record.
    """
    roe  = _safe(row, "roe")
    roa  = _safe(row, "roa")
    npm  = _safe(row, "net_profit_margin")   # ratio e.g. 0.11

    pts = 0.0
    n   = 0

    # ROE (max 2 pts)
    if roe is not None:
        good = ROE_GOOD.get(sector, 0.15)
        if   roe > 0.25:   pts += 2.0
        elif roe > 0.18:   pts += 1.6
        elif roe > good:   pts += 1.2
        elif roe > 0.08:   pts += 0.6
        elif roe > 0:      pts += 0.2
        n += 1

    # ROA (max 1.5 pts)
    if roa is not None:
        if   roa > 0.12:   pts += 1.5
        elif roa > 0.08:   pts += 1.1
        elif roa > 0.05:   pts += 0.7
        elif roa > 0:      pts += 0.3
        n += 1

    # Net profit margin (max 1.5 pts)
    if npm is not None:
        if   npm > 0.20:   pts += 1.5
        elif npm > 0.12:   pts += 1.1
        elif npm > 0.07:   pts += 0.7
        elif npm > 0:      pts += 0.3
        n += 1

    if n == 0:
        return 2.5
    max_pts = (2.0 if roe is not None else 0) + \
              (1.5 if roa is not None else 0) + \
              (1.5 if npm is not None else 0)
    return _clamp((pts / max_pts) * 5.0) if max_pts > 0 else 2.5


# ── 4. HEALTH score ────────────────────────────────────────────────────────────
def score_health(row: dict, sector: str) -> float:
    """
    Score 0–5 based on balance sheet strength.
    Different thresholds for banks (normally high leverage).
    """
    cr  = _safe(row, "current_ratio")
    de  = _safe(row, "de_ratio")       # D/E
    ic  = _safe(row, "interest_coverage")

    pts = 0.0
    n   = 0

    if sector == "bank":
        # Banks: current_ratio not meaningful; use D/E and leverage
        le = _safe(row, "le_ratio")
        if le is not None:
            if   le < 5:   pts += 3.0
            elif le < 8:   pts += 2.0
            elif le < 12:  pts += 1.0
            else:          pts += 0.5
            n += 1
        if ic is not None:
            if   ic > 5:   pts += 2.0
            elif ic > 2:   pts += 1.0
            elif ic > 1:   pts += 0.5
            else:          pts += 0.0
            n += 1
    else:
        # Non-bank
        # Current ratio (max 2 pts)
        if cr is not None:
            if   cr > 2.5:   pts += 2.0
            elif cr > 1.8:   pts += 1.5
            elif cr > 1.2:   pts += 1.0
            elif cr > 1.0:   pts += 0.5
            else:            pts += 0.0
            n += 1

        # D/E ratio (max 1.5 pts) — lower = safer
        if de is not None:
            if   de < 0.2:   pts += 1.5
            elif de < 0.5:   pts += 1.1
            elif de < 1.0:   pts += 0.7
            elif de < 2.0:   pts += 0.3
            else:            pts += 0.0
            n += 1

        # Interest coverage (max 1.5 pts) — higher = safer (or None = no debt)
        if ic is not None:
            if   ic > 10:   pts += 1.5
            elif ic > 5:    pts += 1.1
            elif ic > 2:    pts += 0.7
            elif ic > 1:    pts += 0.3
            else:           pts += 0.0
            n += 1
        elif de is not None and de < 0.1:
            # Virtually debt-free → full health pts
            pts += 1.5
            n += 1

    if n == 0:
        return 2.5
    max_possible = 5.0
    return _clamp((pts / max_possible) * 5.0)


# ── 5. DIVIDEND score ──────────────────────────────────────────────────────────
def score_dividend(row: dict, sector: str) -> float:
    """
    Score 0–5 based on dividend attractiveness.
    """
    dy = _safe(row, "dividend_yield")   # already in % from fetch script

    if dy is None:
        return 0.0

    if   dy > 8:    return 5.0
    elif dy > 5:    return 4.0
    elif dy > 3:    return 3.0
    elif dy > 1.5:  return 2.0
    elif dy > 0:    return 1.0
    else:           return 0.0


# ── Compute all 5 scores for one ticker ───────────────────────────────────────
def calc_snowflake_scores(row: dict, sector: str) -> dict:
    return {
        "score_value":    round(score_value(row, sector),    2),
        "score_future":   round(score_future(row, sector),   2),
        "score_past":     round(score_past(row, sector),     2),
        "score_health":   round(score_health(row, sector),   2),
        "score_dividend": round(score_dividend(row, sector), 2),
    }


# ── Supabase helpers ──────────────────────────────────────────────────────────
def get_sb():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL / SUPABASE_KEY missing")
    from supabase import create_client
    return create_client(url, key)


def fetch_tickers_with_overview(sb) -> list[dict]:
    """Pull all rows from company_overview that have at least pe_ratio."""
    resp = sb.table("company_overview").select("*").execute()
    return resp.data or []


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="V3 P1.4 — Calc Snowflake Scores -> company_overview"
    )
    parser.add_argument("--ticker",  help="Single ticker (default: all in DB)")
    parser.add_argument("--dry-run", action="store_true", help="Print scores, don't write")
    args = parser.parse_args()

    sb = get_sb()

    print(f"\n{'='*60}")
    print(f"  Finsang V3 — Snowflake Score Calculator (P1.4)")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'WRITE TO company_overview'}")
    print(f"{'='*60}\n")

    rows = fetch_tickers_with_overview(sb)
    if args.ticker:
        rows = [r for r in rows if r.get("ticker") == args.ticker.upper()]

    if not rows:
        print("  No company_overview rows found. Run fetch_company_overview.py first.")
        return

    print(f"  Computing scores for {len(rows)} tickers...\n")
    ok = 0

    for row in rows:
        ticker = row.get("ticker", "??")
        sector = row.get("sector") or get_sector(ticker)
        scores = calc_snowflake_scores(row, sector)

        total_pct = round(sum(scores.values()) / (5 * 5) * 100, 0)
        score_str = "  ".join(f"{k.replace('score_','')[0].upper()}={v:.1f}" for k, v in scores.items())
        print(f"  {ticker:6s}: {score_str}  => {total_pct:.0f}%")

        if not args.dry_run:
            sb.table("company_overview").update(scores).eq("ticker", ticker).execute()
        ok += 1

    print(f"\n  Done: {ok} tickers scored.\n")


if __name__ == "__main__":
    main()
