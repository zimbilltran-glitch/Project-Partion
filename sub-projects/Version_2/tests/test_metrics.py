import pytest
import pandas as pd
from unittest.mock import patch

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from metrics import calc_metrics

def mock_load_tab(ticker: str, period: str, sheet: str) -> pd.DataFrame:
    if sheet.lower() == "kqkd":
        return pd.DataFrame({
            "field_id": ["kqkd_doanh_thu_thuan", "kqkd_loi_nhuan_gop", "kqkd_loi_nhuan_cua_co_dong_cua_cong_ty_me"],
            "vn_name": ["Doanh thu", "LN gộp", "LN ròng"],
            "unit": ["VND", "VND", "VND"],
            "level": [1, 1, 1],
            "2023": [1000.0, 200.0, 50.0],
            "2022": [800.0, 100.0, 20.0]
        })
    elif sheet.lower() == "cdkt":
        return pd.DataFrame({
            "field_id": ["cdkt_tai_san_ngan_han", "cdkt_no_ngan_han", "cdkt_no_phai_tra", "cdkt_von_chu_so_huu"],
            "vn_name": ["TS ngắn", "Nợ ngắn", "Tổng Nợ", "VCSH"],
            "unit": ["VND", "VND", "VND", "VND"],
            "level": [1, 1, 1, 1],
            "2023": [500.0, 250.0, 300.0, 400.0],
            "2022": [400.0, 200.0, 250.0, 300.0]
        })
    return pd.DataFrame()

@patch("metrics.load_tab", side_effect=mock_load_tab)
def test_calc_metrics(mock_load):
    df = calc_metrics("VHC", "year")
    
    assert len(df) == 4
    
    gm_row = df[df['field_id'] == 'cstc1'].iloc[0]
    assert gm_row["2023"] == 20.0
    assert gm_row["2022"] == 12.5
    
    nm_row = df[df['field_id'] == 'cstc2'].iloc[0]
    assert nm_row["2023"] == 5.0
    assert nm_row["2022"] == 2.5
    
    cr_row = df[df['field_id'] == 'cstc3'].iloc[0]
    assert cr_row["2023"] == 2.0
    assert cr_row["2022"] == 2.0

    de_row = df[df['field_id'] == 'cstc4'].iloc[0]
    assert de_row["2023"] == 0.75
    assert de_row["2022"] == 0.8333333333333334  # ~0.83
