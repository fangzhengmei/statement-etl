import pandas as pd
from typing import Dict, Any, List
import re

from src.adapters.base import BaseBankAdapter


class ICBCAdapter(BaseBankAdapter):
    bank_type: str = "icbc"
    
    EXPECTED_COLUMNS = {
        "交易日期", "交易时间", "账号", "交易金额", 
        "交易余额", "交易类型", "交易描述", "对手信息"
    }
    
    def detect_format(self, df: pd.DataFrame) -> bool:
        columns = set(df.columns.str.strip())
        return columns >= self.EXPECTED_COLUMNS or \
               any("交易日期" in col and "交易金额" in col for col in columns)
    
    def parse(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        transactions = []
        
        for _, row in df.iterrows():
            try:
                transaction_date = self.normalize_date(
                    str(row.get("交易日期", ""))
                )
                
                amount_str = str(row.get("交易金额", "0"))
                amount = self.normalize_amount(amount_str)
                
                balance_str = str(row.get("交易余额", ""))
                balance = self.normalize_amount(balance_str) if balance_str else None
                
                description = str(row.get("交易描述", "")).strip()
                counterparty = str(row.get("对手信息", "")).strip()
                
                if not counterparty:
                    counterparty = self.extract_counterparty(description)
                
                transaction = {
                    "transaction_date": transaction_date,
                    "transaction_time": str(row.get("交易时间", "")).strip(),
                    "account": str(row.get("账号", "")).strip(),
                    "amount": amount,
                    "balance": balance,
                    "transaction_type": str(row.get("交易类型", "")).strip(),
                    "description": description,
                    "counterparty": counterparty,
                    "category": None,
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                raise ValueError(f"解析行失败: {str(e)}")
        
        return transactions
