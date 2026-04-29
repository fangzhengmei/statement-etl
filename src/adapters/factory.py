import pandas as pd
from typing import Dict, Any, Optional, List

from src.adapters.base import BaseBankAdapter
from src.adapters.icbc import ICBCAdapter
from src.adapters.cmb import CMBAdapter


class AdapterFactory:
    def __init__(self):
        self._adapters: Dict[str, BaseBankAdapter] = {
            "icbc": ICBCAdapter(),
            "cmb": CMBAdapter(),
        }
    
    def get_adapter(self, bank_type: str) -> Optional[BaseBankAdapter]:
        return self._adapters.get(bank_type.lower())
    
    def detect_adapter(self, df: pd.DataFrame) -> Optional[BaseBankAdapter]:
        for adapter in self._adapters.values():
            try:
                if adapter.detect_format(df):
                    return adapter
            except Exception:
                continue
        
        return None
    
    def register_adapter(self, bank_type: str, adapter: BaseBankAdapter):
        self._adapters[bank_type.lower()] = adapter
    
    def list_supported_banks(self) -> List[str]:
        return list(self._adapters.keys())
