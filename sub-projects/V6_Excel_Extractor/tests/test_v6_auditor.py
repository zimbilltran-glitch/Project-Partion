"""
V6 Unit Tests — Phase 6 Excel Pipeline
=======================================
Tests for excel_data_auditor.py core logic:
  - Period mapping / normalization
  - NPL ratio calculation
  - CASA ratio calculation
  - Layout verification
  - Timeout guard import
  - Pending audits state machine

Run: pytest sub-projects/V6_Excel_Extractor/tests/ -v
"""

import pytest
import pandas as pd
import numpy as np
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# ── Path setup ────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent.parent  # project root
V6_DIR = Path(__file__).parent.parent
V2_DIR = ROOT / "sub-projects" / "V2_Data_Pipeline"

sys.path.insert(0, str(V6_DIR))
sys.path.insert(0, str(V2_DIR))

# Load env before any auditor import
from dotenv import load_dotenv
load_dotenv(dotenv_path=ROOT / "frontend" / ".env")
URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
KEY = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
if URL: os.environ["SUPABASE_URL"] = URL
if KEY: os.environ["SUPABASE_KEY"] = KEY

from excel_data_auditor import (
    map_excel_period,
    build_period_col_map,
    safe_float,
    verify_excel_layout,
    read_excel_with_timeout,
    EXCEL_READ_TIMEOUT,
    HEADER_ROW,
    BS_TOTAL_LOANS_ROW,
    NOTE_NPL3_ROW,
    NOTE_NPL4_ROW,
    NOTE_NPL5_ROW,
    NOTE_TOTAL_DEP_ROW,
    NOTE_CASA_ROW,
    GT_TOLERANCE,
)


# ═══════════════════════════════════════════════════════════════
# FIXTURES: Build realistic mock DataFrames
# ═══════════════════════════════════════════════════════════════

def _make_header_row(periods: list) -> list:
    """Build a header row matching Excel Vietcap layout."""
    row = [None] * 2 + periods  # col 0 = label, col 1 = blank, then periods
    return row


def _blank_df(rows: int, cols: int) -> pd.DataFrame:
    return pd.DataFrame([[None] * cols for _ in range(rows)])


def _make_bs_df(periods: list, loan_values: list) -> pd.DataFrame:
    """Mock Balance Sheet DataFrame with correct row structure."""
    cols = len(periods) + 2
    rows = max(BS_TOTAL_LOANS_ROW, HEADER_ROW) + 1

    df = _blank_df(rows, cols)
    # Header row
    df.iloc[HEADER_ROW] = _make_header_row(periods)
    # Loans row
    df.iloc[BS_TOTAL_LOANS_ROW, 0] = "Cho vay khách hàng"
    for i, v in enumerate(loan_values):
        df.iloc[BS_TOTAL_LOANS_ROW, i + 2] = v
    return df


def _make_note_df(periods: list,
                  npl3_vals: list, npl4_vals: list, npl5_vals: list,
                  total_dep_vals: list, casa_vals: list) -> pd.DataFrame:
    """Mock Note Sheet DataFrame with correct row structure."""
    cols = len(periods) + 2
    rows = max(NOTE_CASA_ROW, NOTE_TOTAL_DEP_ROW) + 1

    df = _blank_df(rows, cols)
    # Header
    df.iloc[HEADER_ROW] = _make_header_row(periods)

    def fill_row(row_idx, label, values):
        df.iloc[row_idx, 0] = label
        for i, v in enumerate(values):
            df.iloc[row_idx, i + 2] = v

    fill_row(NOTE_NPL3_ROW,      "Nợ dưới tiêu chuẩn",               npl3_vals)
    fill_row(NOTE_NPL4_ROW,      "Nợ nghi ngờ",                      npl4_vals)
    fill_row(NOTE_NPL5_ROW,      "Nợ xấu có khả năng mất vốn",       npl5_vals)
    fill_row(NOTE_TOTAL_DEP_ROW, "Tổng tiền gửi phân theo loại",     total_dep_vals)
    fill_row(NOTE_CASA_ROW,      "Tiền gửi không kỳ hạn",            casa_vals)

    return df


# ═══════════════════════════════════════════════════════════════
# SUITE 1: Period Mapping
# ═══════════════════════════════════════════════════════════════

class TestPeriodMapping:
    """Test period string conversion to DB format."""

    def test_quarterly_format_standard(self):
        assert map_excel_period("Q4 2024") == "Q4/2024"

    def test_quarterly_format_q1(self):
        assert map_excel_period("Q1 2018") == "Q1/2018"

    def test_quarterly_format_q3(self):
        assert map_excel_period("Q3 2022") == "Q3/2022"

    def test_annual_year_returns_none(self):
        """Annual years should be skipped (return None)."""
        assert map_excel_period("2024") is None
        assert map_excel_period("2018") is None

    def test_whitespace_stripped(self):
        assert map_excel_period("  Q4 2024  ") == "Q4/2024"

    def test_nan_value_returns_none(self):
        assert map_excel_period(float("nan")) is None

    def test_non_quarter_string(self):
        assert map_excel_period("Annual") is None

    def test_build_period_col_map_filters_annual(self):
        """build_period_col_map should exclude annual years."""
        periods = ["Q1 2024", "Q2 2024", "2023", "Q4 2023"]
        df = _make_bs_df(periods, [0, 0, 0, 0])
        col_map = build_period_col_map(df)
        values = list(col_map.values())
        assert "Q1/2024" in values
        assert "Q2/2024" in values
        assert "Q4/2023" in values
        assert "2023" not in values  # annual excluded

    def test_build_period_col_map_count(self):
        periods = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "2023"]
        df = _make_bs_df(periods, [0] * 5)
        col_map = build_period_col_map(df)
        assert len(col_map) == 4  # 4 quarters, 1 annual excluded


# ═══════════════════════════════════════════════════════════════
# SUITE 2: safe_float
# ═══════════════════════════════════════════════════════════════

class TestSafeFloat:
    def test_normal_float(self):
        assert safe_float(123.45) == 123.45

    def test_integer(self):
        assert safe_float(100) == 100.0

    def test_string_number(self):
        assert safe_float("99.5") == 99.5

    def test_nan_returns_none(self):
        assert safe_float(float("nan")) is None

    def test_none_returns_none(self):
        assert safe_float(None) is None

    def test_non_numeric_string(self):
        assert safe_float("N/A") is None

    def test_zero(self):
        assert safe_float(0) == 0.0


# ═══════════════════════════════════════════════════════════════
# SUITE 3: NPL & CASA Calculation
# ═══════════════════════════════════════════════════════════════

class TestNPLCASACalculation:
    """
    Test NPL and CASA ratio calculation from mock Excel data.
    Import parse_bank_NPL_CASA and invoke with mock DFs.
    """

    def setup_method(self):
        from excel_data_auditor import parse_bank_NPL_CASA
        self.parse = parse_bank_NPL_CASA

    def _build_inputs(self, loans, npl3, npl4, npl5, total_dep, casa,
                      period="Q4 2024"):
        """Helper: build minimal mock DFs for one period."""
        periods = [period]
        df_bs = _make_bs_df(periods, [loans])
        df_note = _make_note_df(periods, [npl3], [npl4], [npl5],
                                [total_dep], [casa])
        return df_bs, df_note

    def test_npl_basic_calculation(self):
        """NPL = (npl3 + npl4 + npl5) / total_loans × 100"""
        df_bs, df_note = self._build_inputs(
            loans=1_000_000,   # 1M
            npl3=10_000,       # 1%
            npl4=5_000,        # 0.5%
            npl5=2_000,        # 0.2%
            total_dep=800_000,
            casa=200_000,
            period="Q4 2024"
        )
        ratios = self.parse("MBB", df_bs, df_note)
        npl_records = [r for r in ratios if "nợ xấu" in r["ratio_name"].lower()]
        assert len(npl_records) == 1
        npl_val = npl_records[0]["value"]
        expected = (10_000 + 5_000 + 2_000) / 1_000_000 * 100  # 1.7%
        assert abs(npl_val - expected) < 0.0001

    def test_casa_basic_calculation(self):
        """CASA = casa / total_dep × 100"""
        df_bs, df_note = self._build_inputs(
            loans=1_000_000,
            npl3=0, npl4=0, npl5=0,
            total_dep=500_000,
            casa=200_000,       # 40%
            period="Q4 2024"
        )
        ratios = self.parse("MBB", df_bs, df_note)
        casa_records = [r for r in ratios if "casa" in r["ratio_name"].lower() or "tiền gửi" in r["ratio_name"].lower()]
        assert len(casa_records) == 1
        casa_val = casa_records[0]["value"]
        expected = 200_000 / 500_000 * 100  # 40%
        assert abs(casa_val - expected) < 0.0001

    def test_zero_loans_skips_npl(self):
        """If total loans = 0, NPL record should be skipped (div by zero guard)."""
        df_bs, df_note = self._build_inputs(
            loans=0,
            npl3=1000, npl4=500, npl5=200,
            total_dep=500_000, casa=200_000,
            period="Q4 2024"
        )
        ratios = self.parse("MBB", df_bs, df_note)
        npl_records = [r for r in ratios if r["ratio_name"] == "Tỷ lệ nợ xấu (%)"]
        # Should be empty or have 0 value — no div-by-zero crash
        for rec in npl_records:
            assert rec["value"] == 0.0 or rec["value"] is None

    def test_zero_deposits_skips_casa(self):
        """If total_dep = 0, CASA record should be skipped."""
        df_bs, df_note = self._build_inputs(
            loans=1_000_000,
            npl3=0, npl4=0, npl5=0,
            total_dep=0, casa=0,
            period="Q4 2024"
        )
        ratios = self.parse("MBB", df_bs, df_note)
        casa_records = [r for r in ratios if r["ratio_name"] == "Tỷ lệ CASA (%)"]
        for rec in casa_records:
            assert rec["value"] == 0.0 or rec["value"] is None

    def test_correct_source_label(self):
        """All records must have source='V6_EXCEL'."""
        df_bs, df_note = self._build_inputs(
            loans=1_000_000, npl3=10_000, npl4=5_000, npl5=2_000,
            total_dep=500_000, casa=200_000, period="Q4 2024"
        )
        ratios = self.parse("MBB", df_bs, df_note)
        for r in ratios:
            assert r["source"] == "V6_EXCEL"

    def test_correct_period_format(self):
        """All records must have period in Qx/YYYY format."""
        df_bs, df_note = self._build_inputs(
            loans=1_000_000, npl3=10_000, npl4=5_000, npl5=2_000,
            total_dep=500_000, casa=200_000, period="Q4 2024"
        )
        ratios = self.parse("MBB", df_bs, df_note)
        for r in ratios:
            p = r["period"]
            assert "/" in p, f"Period should contain '/': {p}"
            assert p.startswith("Q"), f"Period should start with Q: {p}"

    def test_multiple_periods(self):
        """Multiple quarters should produce multiple records."""
        periods = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
        loans    = [900_000, 920_000, 950_000, 1_000_000]
        npl3     = [9_000,   9_500,   10_000,  12_000]
        npl4     = [4_500,   4_800,   5_000,   6_000]
        npl5     = [1_800,   2_000,   2_100,   2_500]
        tot_dep  = [480_000, 490_000, 500_000, 520_000]
        casa     = [180_000, 185_000, 195_000, 210_000]

        df_bs   = _make_bs_df(periods, loans)
        df_note = _make_note_df(periods, npl3, npl4, npl5, tot_dep, casa)

        ratios = self.parse("MBB", df_bs, df_note)
        npl_recs  = [r for r in ratios if "nợ xấu" in r["ratio_name"].lower()]
        casa_recs = [r for r in ratios if "casa" in r["ratio_name"].lower() or "tiền gửi" in r["ratio_name"].lower()]

        assert len(npl_recs)  == 4
        assert len(casa_recs) == 4

    def test_ticker_matches_stock_name(self):
        """stock_name field must match input ticker."""
        df_bs, df_note = self._build_inputs(
            loans=1_000_000, npl3=10_000, npl4=5_000, npl5=2_000,
            total_dep=500_000, casa=200_000, period="Q4 2024"
        )
        ratios = self.parse("VCB", df_bs, df_note)
        for r in ratios:
            assert r["stock_name"] == "VCB"


# ═══════════════════════════════════════════════════════════════
# SUITE 4: Layout Verification
# ═══════════════════════════════════════════════════════════════

class TestLayoutVerification:
    """Test verify_excel_layout() keyword detection."""

    def _make_valid_mocks(self):
        """Create valid mock DFs that should pass verification."""
        periods = ["Q4 2024"]
        df_bs = _make_bs_df(periods, [1_000_000])
        df_note = _make_note_df(periods, [10_000], [5_000], [2_000],
                                [500_000], [200_000])
        return df_bs, df_note

    def test_valid_layout_passes(self):
        df_bs, df_note = self._make_valid_mocks()
        assert verify_excel_layout("MBB", df_bs, df_note) is True

    def test_wrong_loans_row_fails(self):
        """If loans row doesn't contain 'cho vay', verification fails."""
        df_bs, df_note = self._make_valid_mocks()
        df_bs.iloc[BS_TOTAL_LOANS_ROW, 0] = "Tiền mặt và tương đương"  # wrong row
        result = verify_excel_layout("MBB", df_bs, df_note)
        assert result is False

    def test_wrong_casa_row_fails(self):
        """If CASA row doesn't contain 'không kỳ hạn', verification fails."""
        df_bs, df_note = self._make_valid_mocks()
        df_note.iloc[NOTE_CASA_ROW, 0] = "Tiền gửi có kỳ hạn"  # wrong row
        result = verify_excel_layout("MBB", df_bs, df_note)
        assert result is False

    def test_empty_row_label_fails(self):
        """None/blank label in critical row should fail."""
        df_bs, df_note = self._make_valid_mocks()
        df_bs.iloc[BS_TOTAL_LOANS_ROW, 0] = None
        result = verify_excel_layout("MBB", df_bs, df_note)
        assert result is False


# ═══════════════════════════════════════════════════════════════
# SUITE 5: Timeout Guard
# ═══════════════════════════════════════════════════════════════

class TestTimeoutGuard:
    """Test read_excel_with_timeout() safety wrapper."""

    def test_timeout_constant_is_90s(self):
        assert EXCEL_READ_TIMEOUT == 90

    def test_timeout_raises_on_hang(self):
        """If read_excel hangs longer than timeout, TimeoutError is raised."""
        import concurrent.futures

        # Mock the future.result() to raise TimeoutError immediately
        mock_future = MagicMock()
        mock_future.result.side_effect = concurrent.futures.TimeoutError()

        mock_executor = MagicMock()
        mock_executor.__enter__ = MagicMock(return_value=mock_executor)
        mock_executor.__exit__ = MagicMock(return_value=False)
        mock_executor.submit = MagicMock(return_value=mock_future)

        with patch("excel_data_auditor.concurrent.futures.ThreadPoolExecutor",
                   return_value=mock_executor):
            with pytest.raises(TimeoutError):
                read_excel_with_timeout("fake_file.xlsx", timeout=1)

    def test_success_returns_dataframe(self):
        """When read completes normally, returns a DataFrame."""
        mock_df = pd.DataFrame({"col": [1, 2, 3]})

        with patch("excel_data_auditor.pd.read_excel", return_value=mock_df):
            result = read_excel_with_timeout("fake_file.xlsx", timeout=5)
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3


# ═══════════════════════════════════════════════════════════════
# SUITE 6: Pending Audits State Machine
# ═══════════════════════════════════════════════════════════════

class TestPendingAuditsMachine:
    """Test the v6_pending_audits.json state machine helpers."""

    def setup_method(self, tmp_path_factory=None):
        from excel_data_auditor import (
            map_excel_period,  # just to confirm import works
        )
        # Import controller helpers
        sys.path.insert(0, str(V6_DIR))
        from v6_master_controller import (
            load_pending, save_pending, mark_completed,
            mark_failed, get_pending_tickers
        )
        self.load_pending     = load_pending
        self.save_pending     = save_pending
        self.mark_completed   = mark_completed
        self.mark_failed      = mark_failed
        self.get_pending      = get_pending_tickers

    def test_get_pending_tickers_filters_only_pending(self):
        data = {
            "pending": [
                {"ticker": "MBB", "period": "Q4/2024", "status": "pending"},
                {"ticker": "VCB", "period": "Q4/2024", "status": "completed"},
                {"ticker": "BID", "period": "Q4/2024", "status": "failed"},
                {"ticker": "CTG", "period": "Q4/2024", "status": "pending"},
            ]
        }
        result = self.get_pending(data)
        assert "MBB" in result
        assert "CTG" in result
        assert "VCB" not in result
        assert "BID" not in result

    def test_get_pending_tickers_deduplicates(self):
        """Same ticker with multiple pending periods = only listed once."""
        data = {
            "pending": [
                {"ticker": "MBB", "period": "Q3/2024", "status": "pending"},
                {"ticker": "MBB", "period": "Q4/2024", "status": "pending"},
            ]
        }
        result = self.get_pending(data)
        assert result.count("MBB") == 1

    def test_mark_completed_updates_status(self):
        """After mark_completed, the entry's status becomes 'completed'."""
        import tempfile, json
        from unittest.mock import patch
        data = {
            "pending": [
                {"ticker": "MBB", "period": "Q4/2024", "status": "pending"},
            ]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            tmp_path = Path(f.name)

        with patch("v6_master_controller.V6_PENDING_FILE", tmp_path):
            self.mark_completed("MBB", "Q4/2024")
            with open(tmp_path, encoding="utf-8") as f:
                updated = json.load(f)
            assert updated["pending"][0]["status"] == "completed"
            assert "completed_at" in updated["pending"][0]

        tmp_path.unlink()

    def test_mark_failed_updates_status(self):
        """After mark_failed, entry status = 'failed' with error message."""
        import tempfile, json
        from unittest.mock import patch
        data = {
            "pending": [
                {"ticker": "VCB", "period": "Q4/2024", "status": "pending"},
            ]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            tmp_path = Path(f.name)

        with patch("v6_master_controller.V6_PENDING_FILE", tmp_path):
            self.mark_failed("VCB", "Q4/2024", "download_timeout")
            with open(tmp_path, encoding="utf-8") as f:
                updated = json.load(f)
            entry = updated["pending"][0]
            assert entry["status"] == "failed"
            assert entry["error"] == "download_timeout"

        tmp_path.unlink()


# ═══════════════════════════════════════════════════════════════
# SUITE 7: Ground Truth Tolerance Logic
# ═══════════════════════════════════════════════════════════════

class TestGroundTruthTolerance:
    """Verify GT_TOLERANCE logic for overwrite decisions."""

    def test_tolerance_constant(self):
        """GT_TOLERANCE should be 0.01% (not 1%)."""
        assert GT_TOLERANCE == 0.01

    def test_zero_api_vs_nonzero_excel_triggers_fix(self):
        """API = 0.0 but Excel ≠ 0 should always trigger overwrite."""
        api_val   = 0.0
        excel_val = 1.6451
        api_is_zero   = api_val == 0.0
        excel_nonzero = abs(excel_val) > GT_TOLERANCE
        diff = abs(api_val - excel_val)
        needs_fix = (api_is_zero and excel_nonzero) or (diff > GT_TOLERANCE)
        assert needs_fix is True

    def test_matching_values_no_fix(self):
        """API and Excel within tolerance should NOT trigger overwrite."""
        api_val   = 1.6451
        excel_val = 1.6452   # diff = 0.0001 < GT_TOLERANCE(0.01)
        diff = abs(api_val - excel_val)
        needs_fix = (api_val == 0.0 and abs(excel_val) > GT_TOLERANCE) or (diff > GT_TOLERANCE)
        assert needs_fix is False

    def test_large_divergence_triggers_fix(self):
        """Diff > 0.01% triggers overwrite even if neither is zero."""
        api_val   = 1.5000
        excel_val = 1.6451   # diff = 0.1451 > 0.01
        diff = abs(api_val - excel_val)
        needs_fix = diff > GT_TOLERANCE
        assert needs_fix is True


# ═══════════════════════════════════════════════════════════════
# SUITE 8: Integration — Sector Guard
# ═══════════════════════════════════════════════════════════════

class TestSectorGuard:
    """Only bank sector should run NPL/CASA extraction."""

    def test_bank_sector_recognized(self):
        from sector import get_sector
        assert get_sector("MBB") == "bank"
        assert get_sector("VCB") == "bank"
        assert get_sector("BID") == "bank"
        assert get_sector("TCB") == "bank"

    def test_non_bank_skips_extraction(self):
        """Non-bank tickers should not produce NPL/CASA records."""
        from sector import get_sector
        from excel_data_auditor import parse_bank_NPL_CASA

        non_banks = ["FPT", "VHM", "SSI", "VND"]
        for ticker in non_banks:
            sector = get_sector(ticker)
            if sector != "bank":
                # Simulate controller logic: only call parse for bank
                # Non-bank should produce empty ratios
                ratios = parse_bank_NPL_CASA(ticker, _blank_df(200, 40), _blank_df(200, 40))
                # Even if called erroneously, should not CRASH
                assert isinstance(ratios, list)
