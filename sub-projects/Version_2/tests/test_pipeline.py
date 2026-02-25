import pytest
import pandas as pd
from typing import Optional, Dict, Any

import sys
from pathlib import Path

# Add project root to sys.path to allow imports
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import normalize
from providers.base import BaseProvider

class MockProvider(BaseProvider):
    def fetch_section(self, ticker: str, section: str) -> Optional[Dict[str, Any]]:
        if section == "BALANCE_SHEET":
            return {
                "years": [
                    {"yearReport": 2023, "lengthReport": 5, "mock1": 1500.0, "ticker": "VHC"}
                ],
                "quarters": [
                    {"yearReport": 2024, "lengthReport": 1, "mock1": 300.0, "ticker": "VHC"}
                ]
            }
        return None

    def get_api_value(self, row: dict, section: str, sheet_row_idx: int, field_id: str = "") -> float | None:
        if section == "BALANCE_SHEET":
            key = f"mock{sheet_row_idx}"
        else:
            key = f"b_sa{sheet_row_idx}"
        val = row.get(key)
        return float(val) if val is not None else None

def test_normalize_with_mock_provider():
    provider = MockProvider()
    
    schema_fields = [
        {"field_id": "bsa1", "vn_name": "Tài sản ngắn hạn", "unit": "VND", "level": 1, "row_number": 1}
    ]
    
    payload = provider.fetch_section("VHC", "BALANCE_SHEET")
    assert payload is not None
    
    df = normalize(payload, "BALANCE_SHEET", "CDKT", schema_fields, provider)
    
    assert len(df) == 2, "Expected 2 periods (1 year, 1 quarter) to be normalized"
    assert "period_type" in df.columns
    
    year_rows = df[df["period_type"] == "year"]
    assert len(year_rows) == 1
    assert year_rows.iloc[0]["period_label"] == "2023"
    assert year_rows.iloc[0]["value"] == 1500.0
    
    q_rows = df[df["period_type"] == "quarter"]
    assert len(q_rows) == 1
    assert q_rows.iloc[0]["period_label"] == "Q1/2024"
    assert q_rows.iloc[0]["value"] == 300.0
