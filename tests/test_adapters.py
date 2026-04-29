import os
import pytest
import tempfile
import shutil

from src.adapters.factory import AdapterFactory
from src.adapters.icbc import ICBCAdapter
from src.adapters.cmb import CMBAdapter
from src.database import DatabaseManager


class TestAdapterFactory:
    def test_factory_can_create_icbc_adapter(self):
        factory = AdapterFactory()
        adapter = factory.get_adapter("icbc")
        assert adapter is not None
        assert adapter.bank_type == "icbc"
    
    def test_factory_can_create_cmb_adapter(self):
        factory = AdapterFactory()
        adapter = factory.get_adapter("cmb")
        assert adapter is not None
        assert adapter.bank_type == "cmb"
    
    def test_factory_returns_none_for_unknown_bank(self):
        factory = AdapterFactory()
        adapter = factory.get_adapter("unknown_bank")
        assert adapter is None


class TestICBCAdapter:
    def test_adapter_has_correct_bank_type(self):
        adapter = ICBCAdapter()
        assert adapter.bank_type == "icbc"
    
    def test_normalize_date_yyyy_mm_dd(self):
        adapter = ICBCAdapter()
        result = adapter.normalize_date("2024-01-15")
        assert result == "2024-01-15"
    
    def test_normalize_date_yyyy_slash_mm_slash_dd(self):
        adapter = ICBCAdapter()
        result = adapter.normalize_date("2024/01/15")
        assert result == "2024-01-15"
    
    def test_normalize_date_dd_slash_mm_slash_yyyy(self):
        adapter = ICBCAdapter()
        result = adapter.normalize_date("15/01/2024")
        assert result == "2024-01-15"
    
    def test_normalize_date_yyyymmdd(self):
        adapter = ICBCAdapter()
        result = adapter.normalize_date("20240115")
        assert result == "2024-01-15"
    
    def test_normalize_amount_positive(self):
        adapter = ICBCAdapter()
        result = adapter.normalize_amount("1,234.56")
        assert result == 1234.56
    
    def test_normalize_amount_negative(self):
        adapter = ICBCAdapter()
        result = adapter.normalize_amount("-1,234.56")
        assert result == -1234.56
    
    def test_normalize_amount_with_currency_symbol(self):
        adapter = ICBCAdapter()
        result = adapter.normalize_amount("￥1,234.56")
        assert result == 1234.56
    
    def test_extract_counterparty_from_description(self):
        adapter = ICBCAdapter()
        desc = "支付宝-星巴克咖啡"
        result = adapter.extract_counterparty(desc)
        assert result == "星巴克咖啡"
    
    def test_extract_counterparty_from_payer(self):
        adapter = ICBCAdapter()
        desc = "付款人：张三 转账"
        result = adapter.extract_counterparty(desc)
        assert result == "张三"


class TestCMBAdapter:
    def test_adapter_has_correct_bank_type(self):
        adapter = CMBAdapter()
        assert adapter.bank_type == "cmb"
    
    def test_normalize_amount_from_income_expense_columns(self):
        adapter = CMBAdapter()
        result = adapter.normalize_amount("5000.00")
        assert result == 5000.00
