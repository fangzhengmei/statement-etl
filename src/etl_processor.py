import os
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import logging

from src.database import DatabaseManager
from src.adapters.factory import AdapterFactory
from src.classifier import TransactionClassifier
from src.error_handler import ErrorHandler


class ETLProcessor:
    def __init__(self, 
                 db_path: str = "data/transactions.db",
                 config_path: str = "config/config.yaml",
                 error_dir: str = "data/errors"):
        self.db = DatabaseManager(db_path)
        self.adapter_factory = AdapterFactory()
        self.classifier = TransactionClassifier(config_path)
        self.error_handler = ErrorHandler(error_dir)
        
        self.logger = logging.getLogger("etl_processor")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def process_file(self, 
                     file_path: str, 
                     bank_type: Optional[str] = None,
                     skip_idempotency_check: bool = False) -> Dict[str, Any]:
        result = {
            "success": False,
            "file_path": file_path,
            "bank_type": bank_type,
            "records_processed": 0,
            "records_imported": 0,
            "errors": 0,
            "already_imported": False,
            "message": ""
        }
        
        try:
            if not os.path.exists(file_path):
                result["message"] = f"文件不存在: {file_path}"
                self.logger.error(result["message"])
                return result
            
            file_hash = self.db.generate_file_hash(file_path)
            
            if not skip_idempotency_check and self.db.is_file_imported(file_hash):
                result["already_imported"] = True
                result["success"] = True
                result["message"] = f"文件已导入过，跳过: {file_path}"
                self.logger.info(result["message"])
                return result
            
            df = self._read_csv_safely(file_path)
            if df is None or df.empty:
                result["message"] = f"无法读取文件或文件为空: {file_path}"
                self.logger.error(result["message"])
                return result
            
            if bank_type:
                adapter = self.adapter_factory.get_adapter(bank_type)
            else:
                adapter = self.adapter_factory.detect_adapter(df)
            
            if not adapter:
                result["message"] = f"无法识别银行格式: {file_path}"
                self.logger.error(result["message"])
                return result
            
            result["bank_type"] = adapter.bank_type
            self.logger.info(f"使用适配器: {adapter.bank_type}")
            
            transactions, errors = self._parse_with_error_handling(
                df, adapter, file_path
            )
            
            result["records_processed"] = len(transactions) + len(errors)
            result["errors"] = len(errors)
            
            for txn in transactions:
                txn["category"] = self.classifier.classify(
                    txn.get("description", ""),
                    txn.get("amount", 0)
                )
                txn["raw_data"] = str(txn.get("raw_data", ""))
            
            db_result = self.db.import_file_transactional(
                os.path.basename(file_path),
                file_hash,
                adapter.bank_type,
                transactions,
                errors
            )
            
            result["records_imported"] = db_result["records_imported"]
            
            if errors:
                self.error_handler.save_error_records(file_path)
            
            result["success"] = True
            result["message"] = f"处理完成: {db_result['records_imported']} 条记录, {len(errors)} 个错误"
            self.logger.info(result["message"])
            
            return result
            
        except Exception as e:
            result["message"] = f"处理失败: {str(e)}"
            self.logger.error(result["message"], exc_info=True)
            self.error_handler.log_error(
                "CRITICAL",
                f"文件处理异常: {str(e)}",
                file_name=file_path
            )
            return result

    def _read_csv_safely(self, file_path: str) -> Optional[pd.DataFrame]:
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, dtype=str)
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception:
                continue
        
        try:
            df = pd.read_csv(file_path, encoding='latin1', dtype=str)
            return df
        except Exception as e:
            self.logger.error(f"无法读取文件，所有编码尝试失败: {e}")
            return None

    def _parse_with_error_handling(self, 
                                    df: pd.DataFrame, 
                                    adapter,
                                    file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        transactions = []
        errors = []
        
        for idx, row in df.iterrows():
            try:
                row_dict = row.to_dict()
                parsed_list = adapter.parse(pd.DataFrame([row_dict]))
                
                if parsed_list:
                    for txn in parsed_list:
                        txn["raw_data"] = str(row_dict)
                        transactions.append(txn)
                        
            except Exception as e:
                error_msg = f"解析行失败: {str(e)}"
                self.error_handler.log_error(
                    "ERROR",
                    error_msg,
                    row_data=row.to_dict(),
                    row_index=idx,
                    file_name=file_path
                )
                errors.append({
                    "row_index": idx,
                    "row_data": row.to_dict(),
                    "message": error_msg
                })
        
        return transactions, errors

    def process_directory(self, 
                          directory: str,
                          bank_type: Optional[str] = None) -> Dict[str, Any]:
        if not os.path.exists(directory):
            return {
                "success": False,
                "message": f"目录不存在: {directory}",
                "results": []
            }
        
        results = []
        total_processed = 0
        total_imported = 0
        total_errors = 0
        
        for filename in os.listdir(directory):
            if filename.lower().endswith('.csv'):
                file_path = os.path.join(directory, filename)
                result = self.process_file(file_path, bank_type)
                results.append(result)
                
                if result["success"]:
                    total_processed += result["records_processed"]
                    total_imported += result["records_imported"]
                    total_errors += result["errors"]
        
        return {
            "success": True,
            "total_processed": total_processed,
            "total_imported": total_imported,
            "total_errors": total_errors,
            "results": results
        }

    def get_transaction_stats(self) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM transactions')
            total_transactions = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT category, COUNT(*) as cnt, SUM(amount) as total
                FROM transactions 
                GROUP BY category
            ''')
            category_stats = {}
            for row in cursor.fetchall():
                category_stats[row[0]] = {
                    "count": row[1],
                    "total_amount": row[2]
                }
            
            cursor.execute('SELECT COUNT(*) FROM files')
            total_files = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM error_records')
            total_errors = cursor.fetchone()[0]
        
        return {
            "total_transactions": total_transactions,
            "total_files": total_files,
            "total_errors": total_errors,
            "category_stats": category_stats
        }
