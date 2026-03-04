"""
Phase 2 — Sector Intelligence: Centralized Sector Routing Module
sector.py — Single source of truth for ticker → sector classification

Replaces hardcoded BANK_TICKERS / SEC_TICKERS in pipeline.py and metrics.py.
Data source: Supabase `companies` table (seeded via Phase 2 migration).

Sector types:
  'bank'   → Ngân hàng thương mại (MBB, VCB, CTG...)
  'sec'    → Công ty Chứng khoán (SSI, VND, HCM, VCI)
  'normal' → Phi tài chính / Sản xuất / BĐS / Bán lẻ (VHC, HPG, FPT...)

Usage:
  from sector import get_sector, get_company_info, SECTOR_SHEETS
  sector = get_sector("MBB")        # → "bank"
  info   = get_company_info("MBB")  # → {"ticker": "MBB", "company_name": "...", ...}
  sheets = SECTOR_SHEETS["bank"]    # → [("BALANCE_SHEET", "CDKT_BANK"), ...]
"""

import os
from pathlib import Path
from typing import Optional

# ─── Load .env ────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

# ─── Local cache (avoid repeated DB calls) ────────────────────────────────────
_CACHE: dict[str, dict] = {}
_CACHE_LOADED = False


# ─── Sector → Sheet mapping ──────────────────────────────────────────────────
SECTOR_SHEETS = {
    "bank": [
        ("BALANCE_SHEET", "CDKT_BANK"),
        ("INCOME_STATEMENT", "KQKD_BANK"),
        ("CASH_FLOW", "LCTT_BANK"),
    ],
    "sec": [
        ("BALANCE_SHEET", "CDKT_SEC"),
        ("INCOME_STATEMENT", "KQKD_SEC"),
        ("CASH_FLOW", "LCTT_SEC"),
    ],
    "normal": [
        ("BALANCE_SHEET", "CDKT"),
        ("INCOME_STATEMENT", "KQKD"),
        ("CASH_FLOW", "LCTT"),
        ("NOTE", "NOTE"),
    ],
}

# ─── Sector Vietnamese labels ────────────────────────────────────────────────
SECTOR_LABELS = {
    "bank":   "Ngân hàng",
    "sec":    "Chứng khoán",
    "normal": "Phi tài chính",
}


def _load_cache():
    """Load all companies from Supabase into memory cache."""
    global _CACHE, _CACHE_LOADED
    if _CACHE_LOADED:
        return

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("  ⚠️ sector.py: SUPABASE_URL/KEY not set — using fallback")
        _load_fallback()
        return

    try:
        from sb_client import get_sb
        sb = get_sb()
        response = sb.table("companies").select("*").execute()
        for row in response.data:
            _CACHE[row["ticker"]] = row
        _CACHE_LOADED = True
    except Exception as e:
        print(f"  ⚠️ sector.py: Supabase shared client failed ({e}) — trying local create")
        try:
             from supabase import create_client
             sb = create_client(url, key)
             response = sb.table("companies").select("*").execute()
             for row in response.data:
                 _CACHE[row["ticker"]] = row
             _CACHE_LOADED = True
        except Exception as e2:
             print(f"  ⚠️ sector.py: Local create also failed ({e2}) — using fallback")
             _load_fallback()


def _load_fallback():
    """Hardcoded fallback — used only when Supabase is unreachable."""
    global _CACHE, _CACHE_LOADED
    _FALLBACK_BANKS = {"ACB", "BID", "CTG", "HDB", "MBB", "SHB", "SSB", "STB", "TCB", "TPB", "VCB", "VIB", "VPB"}
    _FALLBACK_SECS = {"SSI", "HCM", "VCI", "VND"}

    for t in _FALLBACK_BANKS:
        _CACHE[t] = {"ticker": t, "company_name": f"Ngân hàng {t}", "sector": "bank", "exchange": "HOSE", "in_vn30": True}
    for t in _FALLBACK_SECS:
        _CACHE[t] = {"ticker": t, "company_name": f"CTCK {t}", "sector": "sec", "exchange": "HOSE", "in_vn30": t == "SSI"}
    _CACHE_LOADED = True


def get_sector(ticker: str) -> str:
    """Returns sector string: 'bank', 'sec', or 'normal'."""
    _load_cache()
    info = _CACHE.get(ticker.upper())
    return info["sector"] if info else "normal"


def get_company_info(ticker: str) -> Optional[dict]:
    """Returns full company info dict, or None if not found."""
    _load_cache()
    return _CACHE.get(ticker.upper())


def get_company_name(ticker: str) -> str:
    """Returns company name, or fallback 'CTCP {ticker}'."""
    info = get_company_info(ticker)
    return info["company_name"] if info else f"CTCP {ticker}"


def get_sheets_for_ticker(ticker: str) -> list[tuple[str, str]]:
    """Returns the correct [(API_section, schema_sheet_id)] for this ticker's sector."""
    sector = get_sector(ticker)
    return SECTOR_SHEETS.get(sector, SECTOR_SHEETS["normal"])


def is_bank(ticker: str) -> bool:
    return get_sector(ticker) == "bank"


def is_sec(ticker: str) -> bool:
    return get_sector(ticker) == "sec"


def get_all_tickers(sector: Optional[str] = None, vn30_only: bool = False) -> list[str]:
    """Get all known tickers, optionally filtered by sector and/or VN30."""
    _load_cache()
    result = []
    for t, info in _CACHE.items():
        if sector and info.get("sector") != sector:
            continue
        if vn30_only and not info.get("in_vn30"):
            continue
        result.append(t)
    return sorted(result)


if __name__ == "__main__":
    # Quick test
    _load_cache()
    print(f"Loaded {len(_CACHE)} companies from Supabase")
    for sector_key in ["bank", "sec", "normal"]:
        tickers = get_all_tickers(sector=sector_key)
        print(f"  {SECTOR_LABELS[sector_key]} ({len(tickers)}): {', '.join(tickers)}")
    
    # Test specific lookups
    for t in ["MBB", "SSI", "VHC", "UNKNOWN"]:
        print(f"  {t} → sector={get_sector(t)}, name={get_company_name(t)}")
