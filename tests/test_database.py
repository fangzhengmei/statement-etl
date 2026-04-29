import os
import pytest
import tempfile

from src.database import DatabaseManager


class TestDatabaseManager:
    def test_db_initialization(self, temp_db_path):
        db = DatabaseManager(temp_db_path)
        assert os.path.exists(temp_db_path)
    
    def test_generate_file_hash(self, temp_db_path):
        db = DatabaseManager(temp_db_path)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("test,data\n1,2")
            temp_file = f.name
        
        try:
            file_hash = db.generate_file_hash(temp_file)
            assert file_hash is not None
            assert len(file_hash) > 0
        finally:
            os.unlink(temp_file)
    
    def test_generate_transaction_hash(self, temp_db_path):
        db = DatabaseManager(temp_db_path)
        
        transaction = {
            "transaction_date": "2024-01-01",
            "description": "测试交易",
            "amount": 100.0,
            "balance": 1000.0,
            "counterparty": "测试方"
        }
        
        hash1 = db.generate_transaction_hash(transaction)
        hash2 = db.generate_transaction_hash(transaction)
        
        assert hash1 == hash2
        assert len(hash1) > 0
    
    def test_different_transactions_have_different_hashes(self, temp_db_path):
        db = DatabaseManager(temp_db_path)
        
        txn1 = {
            "transaction_date": "2024-01-01",
            "description": "交易1",
            "amount": 100.0,
            "balance": 1000.0,
            "counterparty": "A"
        }
        
        txn2 = {
            "transaction_date": "2024-01-02",
            "description": "交易2",
            "amount": 200.0,
            "balance": 1200.0,
            "counterparty": "B"
        }
        
        hash1 = db.generate_transaction_hash(txn1)
        hash2 = db.generate_transaction_hash(txn2)
        
        assert hash1 != hash2
    
    def test_create_file_record(self, temp_db_path):
        db = DatabaseManager(temp_db_path)
        
        file_id = db.create_file_record("test.csv", "hash123", "icbc")
        assert file_id > 0
    
    def test_is_file_imported(self, temp_db_path):
        db = DatabaseManager(temp_db_path)
        
        assert not db.is_file_imported("nonexistent_hash")
        
        db.create_file_record("test.csv", "test_hash", "icbc")
        assert db.is_file_imported("test_hash")
    
    def test_insert_transactions(self, temp_db_path):
        db = DatabaseManager(temp_db_path)
        
        file_id = db.create_file_record("test.csv", "hash123", "icbc")
        
        transactions = [
            {
                "transaction_date": "2024-01-01",
                "description": "测试交易",
                "amount": 100.0,
                "balance": 1000.0,
                "counterparty": "测试方",
                "category": "测试分类",
                "raw_data": "test"
            }
        ]
        
        db.insert_transactions(transactions, file_id)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM transactions')
            count = cursor.fetchone()[0]
            assert count == 1
    
    def test_insert_error(self, temp_db_path):
        db = DatabaseManager(temp_db_path)
        
        file_id = db.create_file_record("test.csv", "hash123", "icbc")
        
        db.insert_error(file_id, 1, "raw_data", "测试错误")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM error_records')
            count = cursor.fetchone()[0]
            assert count == 1
