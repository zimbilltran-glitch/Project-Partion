import requests
from typing import Optional, Dict, Any
from .base import BaseProvider

class VietcapProvider(BaseProvider):
    """Data provider for Vietcap IQ API."""
    
    BASE_URL = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/financial-statement?section={section}"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://trading.vietcap.com.vn/",
        "Origin": "https://trading.vietcap.com.vn",
    }
    
    API_PREFIX = {
        "BALANCE_SHEET":    ["bsa", "bsb", "bss", "bsi"],
        "INCOME_STATEMENT": ["isa", "isb", "iss", "isi"],
        "CASH_FLOW":        ["cfa", "cfb", "cfs", "cfi", "cfs"],
        "NOTE":             ["noa", "nob", "nos", "noi"],
    }

    def fetch_section(self, ticker: str, section: str) -> Optional[Dict[str, Any]]:
        url = self.BASE_URL.format(ticker=ticker.upper(), section=section)
        try:
            r = requests.get(url, headers=self.HEADERS, timeout=20)
            r.raise_for_status()
            data = r.json()
            if not data.get("successful"):
                print(f"    ⚠️  Vietcap API returned unsuccessful: {data.get('msg')}")
                return None
            return data.get("data", {})
        except Exception as e:
            print(f"    ❌ Vietcap fetch error for {section}: {e}")
            return None

    def get_api_value(self, row: dict, section: str, sheet_row_idx: int, field_id: str = "") -> Optional[float]:
        # Override specific essential metric fields for accurate mapping
        field_mapping = {
            "cdkt_tai_san_ngan_han": "bsa1",
            "cdkt_tai_san_dai_han": "bsa23",
            "cdkt_tong_cong_tai_san": "bsa96",
            "cdkt_no_phai_tra": "bsa54",
            "cdkt_no_ngan_han": "bsa55",
            "cdkt_no_dai_han": "bsa67",
            "cdkt_von_chu_so_huu": "bsa79",
            "kqkd_doanh_thu_thuan": "isa3",
            "kqkd_loi_nhuan_gop": "isa5",
            "kqkd_loi_nhuan_cua_co_dong_cua_cong_ty_me": "isa22"
        }
        
        if field_id in field_mapping:
            key = field_mapping[field_id]
        else:
            # Vietcap uses dynamic keys based on row indices
            if section == "BALANCE_SHEET":
                key = f"bsa{sheet_row_idx}"
            elif section == "INCOME_STATEMENT":
                key = f"isa{sheet_row_idx}"
            elif section == "CASH_FLOW":
                key = f"cfa{sheet_row_idx}"
            else:
                key = f"b_sa{sheet_row_idx}"
            
        val = row.get(key)
        
        # Additional nested check just in case
        if val is None and isinstance(row.get("values"), dict):
            val = row["values"].get(key)
            
        return float(val) if val is not None else None
