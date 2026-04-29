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
        
        yyyy_mm_dd_patterns = [
            r'^(\d{4})-(\d{1,2})-(\d{1,2})$',
            r'^(\d{4})/(\d{1,2})/(\d{1,2})$',
            r'^(\d{4})(\d{2})(\d{2})$',
        ]
        
        for pattern in yyyy_mm_dd_patterns:
            match = re.match(pattern, date_str)
            if match:
                year, month, day = match.groups()
                try:
                    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
                except ValueError:
                    continue
        
        dd_mm_yyyy_patterns = [
            r'^(\d{1,2})/(\d{1,2})/(\d{4})$',
            r'^(\d{1,2})-(\d{1,2})-(\d{4})$',
        ]
        
        for pattern in dd_mm_yyyy_patterns:
            match = re.match(pattern, date_str)
            if match:
                day, month, year = match.groups()
                day_int = int(day)
                month_int = int(month)
                
                if month_int > 12 and day_int <= 12:
                    month_int, day_int = day_int, month_int
                
                try:
                    return f"{int(year):04d}-{int(month_int):02d}-{int(day_int):02d}"
                except ValueError:
                    continue
        
        return date_str
    
    def normalize_amount(self, amount_str) -> float:
        if pd.isna(amount_str):
            return 0.0
        
        if amount_str is None:
            return 0.0
        
        amount_str = str(amount_str).strip()
        
        if amount_str == "" or amount_str.lower() in ("null", "none", "nan"):
            return 0.0
        
        amount_str = amount_str.replace(',', '')
        amount_str = amount_str.replace('￥', '')
        amount_str = amount_str.replace('¥', '')
        amount_str = amount_str.replace('CNY', '')
        amount_str = amount_str.strip()
        
        if not amount_str:
            return 0.0
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
    def extract_counterparty(self, description: str) -> str:
        if not description or pd.isna(description):
            return ""
        
        description = str(description)
        
        patterns = [
            r'[收付]款人[：:]\s*([^\s，。,；\n]+)',
            r'[转汇]给\s*([^\s，。,；\n]+)',
            r'来自\s*([^\s，。,；\n]+)',
            r'支付宝-\s*([^\s，。,；\n]+)',
            r'微信支付-\s*([^\s，。,；\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(1).strip()
        
        return ""
