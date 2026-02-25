from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseProvider(ABC):
    @abstractmethod
    def fetch_section(self, ticker: str, section: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_api_value(self, row: dict, section: str, sheet_row_idx: int, field_id: str = "") -> Optional[float]:
        pass
