from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List, Optional
import re


class BaseBankAdapter(ABC):
    bank_type: str = "base"
    
    @abstractmethod
    def detect_format(self, df: pd.DataFrame) -> bool:
        pass
    
    @abstractmethod
    def parse(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        pass
    
    def normalize_date(self, date_str: str) -> str:
        date_str = str(date_str).strip()
        
        patterns = [
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', r'\1-\2-\3'),
            (r'(\d{4})/(\d{1,2})/(\d{1,2})', r'\1-\2-\3'),
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', r'\3-\1-\2'),
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', r'\3-\1-\2'),
            (r'(\d{4})(\d{2})(\d{2})', r'\1-\2-\3'),
        ]
        
        for pattern, replacement in patterns:
            match = re.match(pattern, date_str)
            if match:
                try:
                    parts = list(match.groups())
                    year = parts[0] if len(parts[0]) == 4 else parts[2]
                    month = parts[1] if len(parts[0]) == 4 else parts[0]
                    day = parts[2] if len(parts[0]) == 4 else parts[1]
                    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
                except (ValueError, IndexError):
                    continue
        
        return date_str
    
    def normalize_amount(self, amount_str) -> float:
        if pd.isna(amount_str):
            return 0.0
        
        amount_str = str(amount_str).strip()
        amount_str = amount_str.replace(',', '')
        amount_str = amount_str.replace('￥', '')
        amount_str = amount_str.replace('¥', '')
        amount_str = amount_str.replace('CNY', '')
        amount_str = amount_str.strip()
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
    def extract_counterparty(self, description: str) -> str:
        if not description or pd.isna(description):
            return ""
        
        description = str(description)
        
        patterns = [
            r'[收|付]款人[：:]\s*([^，。,；\n]+)',
            r'[转|汇]给\s*([^，。,；\n]+)',
            r'来自\s*([^，。,；\n]+)',
            r'支付宝-\s*([^，。,；\n]+)',
            r'微信支付-\s*([^，。,；\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(1).strip()
        
        return ""
