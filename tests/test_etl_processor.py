import os
import pytest
import tempfile
import shutil
import pandas as pd

from src.etl_processor import ETLProcessor
from src.database import DatabaseManager


class TestETLProcessor:
    def test_processor_initialization(self, temp_db_path, temp_error_dir):
        processor = ETLProcessor(
            db_path=temp_db_path,
            error_dir=temp_error_dir
        )
        assert processor is not None
        assert processor.db is not None
        assert processor.classifier is not None
        assert processor.error_handler is not None
    
    def test_process_icbc_file(self, temp_db_path, temp_error_dir, icbc_test_file):
        processor = ETLProcessor(
            db_path=temp_db_path,
            error_dir=temp_error_dir
        )
        
        result = processor.process_file(icbc_test_file, bank_type="icbc")
        
        assert result["success"] is True
        assert result["already_imported"] is False
        assert result["records_processed"] == 5
        assert result["records_imported"] == 5
        assert result["errors"] == 0
        assert result["bank_type"] == "icbc"
    
    def test_process_cmb_file(self, temp_db_path, temp_error_dir, cmb_test_file):
        processor = ETLProcessor(
            db_path=temp_db_path,
            error_dir=temp_error_dir
        )
        
        result = processor.process_file(cmb_test_file, bank_type="cmb")
        
        assert result["success"] is True
        assert result["already_imported"] is False
        assert result["records_processed"] == 5
        assert result["records_imported"] == 5
        assert result["errors"] == 0
        assert result["bank_type"] == "cmb"
    
    def test_idempotent_import(self, temp_db_path, temp_error_dir, icbc_test_file):
        processor = ETLProcessor(
            db_path=temp_db_path,
            error_dir=temp_error_dir
        )
        
        result1 = processor.process_file(icbc_test_file, bank_type="icbc")
        assert result1["success"] is True
        assert result1["already_imported"] is False
        assert result1["records_imported"] == 5
        
        result2 = processor.process_file(icbc_test_file, bank_type="icbc")
        assert result2["success"] is True
        assert result2["already_imported"] is True
        
        with processor.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM transactions')
            count = cursor.fetchone()[0]
            assert count == 5
    
    def test_skip_idempotency_check(self, temp_db_path, temp_error_dir, icbc_test_file):
        processor = ETLProcessor(
            db_path=temp_db_path,
            error_dir=temp_error_dir
        )
        
        result1 = processor.process_file(icbc_test_file, bank_type="icbc")
        assert result1["records_imported"] == 5
        
        result2 = processor.process_file(
            icbc_test_file, 
            bank_type="icbc",
            skip_idempotency_check=True
        )
        assert result2["already_imported"] is False
        
        with processor.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM transactions')
            count = cursor.fetchone()[0]
            assert count == 5
    
    def test_transaction_classification(self, temp_db_path, temp_error_dir, icbc_test_file):
        processor = ETLProcessor(
            db_path=temp_db_path,
            error_dir=temp_error_dir
        )
        
        processor.process_file(icbc_test_file, bank_type="icbc")
        
        with processor.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT category FROM transactions')
            categories = [row[0] for row in cursor.fetchall()]
            
            assert len(categories) > 0
            assert "未分类" not in categories or len(categories) > 1
    
    def test_nonexistent_file(self, temp_db_path, temp_error_dir):
        processor = ETLProcessor(
            db_path=temp_db_path,
            error_dir=temp_error_dir
        )
        
        result = processor.process_file("/nonexistent/path.csv")
        
        assert result["success"] is False
        assert "不存在" in result["message"]
    
    def test_get_transaction_stats(self, temp_db_path, temp_error_dir, icbc_test_file):
        processor = ETLProcessor(
            db_path=temp_db_path,
            error_dir=temp_error_dir
        )
        
        processor.process_file(icbc_test_file, bank_type="icbc")
        
        stats = processor.get_transaction_stats()
        
        assert stats["total_transactions"] == 5
        assert stats["total_files"] == 1
        assert stats["total_errors"] == 0
        assert len(stats["category_stats"]) > 0
    
    def test_transaction_idempotency_by_hash(self, temp_db_path, temp_error_dir):
        db = DatabaseManager(temp_db_path)
        
        txn1 = {
            "transaction_date": "2024-01-01",
            "description": "测试交易",
            "amount": 100.0,
            "balance": 1000.0,
            "counterparty": "测试方"
        }
        
        txn2 = {
            "transaction_date": "2024-01-01",
            "description": "测试交易",
            "amount": 100.0,
            "balance": 1000.0,
            "counterparty": "测试方"
        }
        
        hash1 = db.generate_transaction_hash(txn1)
        hash2 = db.generate_transaction_hash(txn2)
        
        assert hash1 == hash2
        
        file_id = db.create_file_record("test.csv", "hash123", "icbc")
        
        txn1["category"] = "测试"
        txn1["raw_data"] = ""
        db.insert_transactions([txn1], file_id)
        
        txn2["category"] = "测试"
        txn2["raw_data"] = ""
        db.insert_transactions([txn2], file_id)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM transactions')
            count = cursor.fetchone()[0]
            assert count == 1
