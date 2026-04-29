import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import csv
import json


class ErrorHandler:
    def __init__(self, error_dir: str = "data/errors", log_level: int = logging.INFO):
        self.error_dir = error_dir
        os.makedirs(error_dir, exist_ok=True)
        
        self.logger = logging.getLogger("etl_error_handler")
        self.logger.setLevel(log_level)
        
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            
            log_file = os.path.join(error_dir, f"etl_{datetime.now().strftime('%Y%m%d')}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
        
        self.error_records: List[Dict[str, Any]] = []
        self.error_count = 0

    def log_error(self, error_type: str, message: str, 
                  row_data: Optional[Dict[str, Any]] = None,
                  row_index: Optional[int] = None,
                  file_name: Optional[str] = None):
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": message,
            "row_index": row_index,
            "file_name": file_name,
            "row_data": row_data
        }
        
        self.error_records.append(error_record)
        self.error_count += 1
        
        log_message = f"[{error_type}] {message}"
        if file_name:
            log_message += f" (文件: {file_name})"
        if row_index is not None:
            log_message += f" (行号: {row_index})"
        
        if error_type == "CRITICAL":
            self.logger.critical(log_message)
        elif error_type == "ERROR":
            self.logger.error(log_message)
        elif error_type == "WARNING":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        if row_data:
            self.logger.debug(f"原始数据: {json.dumps(row_data, ensure_ascii=False, default=str)}")

    def save_error_records(self, file_name: str = None):
        if not self.error_records:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if file_name:
            base_name = os.path.splitext(os.path.basename(file_name))[0]
            error_file = os.path.join(self.error_dir, f"{base_name}_errors_{timestamp}.csv")
        else:
            error_file = os.path.join(self.error_dir, f"errors_{timestamp}.csv")
        
        if self.error_records:
            fieldnames = list(self.error_records[0].keys())
            
            with open(error_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for record in self.error_records:
                    writer.writerow({
                        k: json.dumps(v, ensure_ascii=False, default=str) 
                        if isinstance(v, (dict, list)) else v
                        for k, v in record.items()
                    })
        
        self.logger.info(f"错误记录已保存到: {error_file}")

    def clear_errors(self):
        self.error_records = []
        self.error_count = 0

    def get_error_summary(self) -> Dict[str, Any]:
        error_types = {}
        for record in self.error_records:
            err_type = record.get("error_type", "UNKNOWN")
            error_types[err_type] = error_types.get(err_type, 0) + 1
        
        return {
            "total_errors": self.error_count,
            "error_type_counts": error_types,
            "error_records": self.error_records[-10:] if self.error_records else []
        }
