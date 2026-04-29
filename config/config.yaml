import sqlite3
import hashlib
import os
from typing import Optional, Dict, Any, List
import pandas as pd


class DatabaseManager:
    def __init__(self, db_path: str = "data/transactions.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_hash TEXT NOT NULL UNIQUE,
                    bank_type TEXT NOT NULL,
                    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    record_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    UNIQUE(filename, file_hash)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    transaction_hash TEXT NOT NULL UNIQUE,
                    transaction_date DATE NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL,
                    balance REAL,
                    counterparty TEXT,
                    category TEXT,
                    raw_data TEXT,
                    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    row_index INTEGER,
                    raw_data TEXT,
                    error_message TEXT,
                    error_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_hash ON transactions (transaction_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_hash ON files (file_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_date ON transactions (transaction_date)')
            
            conn.commit()

    def generate_file_hash(self, filepath: str) -> str:
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def generate_transaction_hash(self, transaction: Dict[str, Any]) -> str:
        key = (
            str(transaction.get('transaction_date', '')),
            str(transaction.get('description', '')),
            str(transaction.get('amount', 0)),
            str(transaction.get('balance', '')),
            str(transaction.get('counterparty', ''))
        )
        return hashlib.sha256(str(key).encode('utf-8')).hexdigest()

    def is_file_imported(self, file_hash: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM files WHERE file_hash = ?', (file_hash,))
            return cursor.fetchone() is not None

    def is_transaction_imported(self, transaction_hash: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM transactions WHERE transaction_hash = ?', (transaction_hash,))
            return cursor.fetchone() is not None

    def create_file_record(self, filename: str, file_hash: str, bank_type: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO files (filename, file_hash, bank_type)
                VALUES (?, ?, ?)
            ''', (filename, file_hash, bank_type))
            file_id = cursor.lastrowid
            conn.commit()
            return file_id

    def update_file_stats(self, file_id: int, record_count: int, error_count: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE files
                SET record_count = ?, error_count = ?
                WHERE id = ?
            ''', (record_count, error_count, file_id))
            conn.commit()

    def insert_transactions(self, transactions: List[Dict[str, Any]], file_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for txn in transactions:
                txn_hash = self.generate_transaction_hash(txn)
                
                if self.is_transaction_imported(txn_hash):
                    continue
                
                cursor.execute('''
                    INSERT INTO transactions (
                        file_id, transaction_hash, transaction_date, description,
                        amount, balance, counterparty, category, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_id,
                    txn_hash,
                    txn.get('transaction_date'),
                    txn.get('description'),
                    txn.get('amount'),
                    txn.get('balance'),
                    txn.get('counterparty'),
                    txn.get('category'),
                    txn.get('raw_data', '')
                ))
            conn.commit()

    def insert_error(self, file_id: int, row_index: int, raw_data: str, error_message: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO error_records (file_id, row_index, raw_data, error_message)
                VALUES (?, ?, ?, ?)
            ''', (file_id, row_index, raw_data, error_message))
            conn.commit()

    def get_transactions(self, category: Optional[str] = None, 
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> pd.DataFrame:
        query = 'SELECT * FROM transactions WHERE 1=1'
        params = []
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if start_date:
            query += ' AND transaction_date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND transaction_date <= ?'
            params.append(end_date)
        
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
