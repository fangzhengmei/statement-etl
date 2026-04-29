import pandas as pd
from typing import Dict, Any, List

from src.adapters.base import BaseBankAdapter


class CMBAdapter(BaseBankAdapter):
    bank_type: str = "cmb"
    
    EXPECTED_COLUMNS = {
        "记账日期", "交易时间", "交易摘要", "交易金额",
        "联机余额", "交易对手", "交易类型"
    }
    
    def detect_format(self, df: pd.DataFrame) -> bool:
        columns = set(df.columns.str.strip())
        return "记账日期" in columns and ("交易金额" in columns or "收入金额" in columns)
    
    def parse(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        transactions = []
        
        for _, row in df.iterrows():
            try:
                transaction_date = self.normalize_date(
                    str(row.get("记账日期", ""))
                )
                
                amount = 0.0
                if "收入金额" in df.columns and "支出金额" in df.columns:
                    income = self.normalize_amount(str(row.get("收入金额", "0")))
                    expense = self.normalize_amount(str(row.get("支出金额", "0")))
                    amount = income - expense
                else:
                    amount_str = str(row.get("交易金额", "0"))
                    amount = self.normalize_amount(amount_str)
                
                balance_str = str(row.get("联机余额", ""))
                balance = self.normalize_amount(balance_str) if balance_str else None
                
                description = str(row.get("交易摘要", "")).strip()
                counterparty = str(row.get("交易对手", "")).strip()
                
                if not counterparty:
                    counterparty = self.extract_counterparty(description)
                
                transaction = {
                    "transaction_date": transaction_date,
                    "transaction_time": str(row.get("交易时间", "")).strip(),
                    "account": str(row.get("账号", row.get("账户", ""))).strip(),
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
