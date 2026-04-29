import os
import pytest

from src.error_handler import ErrorHandler


class TestErrorHandler:
    def test_error_handler_initialization(self, temp_error_dir):
        handler = ErrorHandler(error_dir=temp_error_dir)
        assert handler is not None
        assert handler.error_count == 0
        assert len(handler.error_records) == 0
    
    def test_log_error(self, temp_error_dir):
        handler = ErrorHandler(error_dir=temp_error_dir)
        
        handler.log_error(
            error_type="ERROR",
            message="测试错误信息",
            row_data={"key": "value"},
            row_index=1,
            file_name="test.csv"
        )
        
        assert handler.error_count == 1
        assert len(handler.error_records) == 1
        
        record = handler.error_records[0]
        assert record["error_type"] == "ERROR"
        assert record["message"] == "测试错误信息"
        assert record["row_index"] == 1
        assert record["file_name"] == "test.csv"
    
    def test_log_multiple_errors(self, temp_error_dir):
        handler = ErrorHandler(error_dir=temp_error_dir)
        
        for i in range(5):
            handler.log_error(
                error_type="ERROR",
                message=f"错误 {i}",
                row_index=i
            )
        
        assert handler.error_count == 5
        assert len(handler.error_records) == 5
    
    def test_clear_errors(self, temp_error_dir):
        handler = ErrorHandler(error_dir=temp_error_dir)
        
        handler.log_error("ERROR", "测试错误")
        assert handler.error_count == 1
        
        handler.clear_errors()
        assert handler.error_count == 0
        assert len(handler.error_records) == 0
    
    def test_get_error_summary(self, temp_error_dir):
        handler = ErrorHandler(error_dir=temp_error_dir)
        
        handler.log_error("ERROR", "错误1")
        handler.log_error("WARNING", "警告1")
        handler.log_error("ERROR", "错误2")
        
        summary = handler.get_error_summary()
        
        assert summary["total_errors"] == 3
        assert summary["error_type_counts"]["ERROR"] == 2
        assert summary["error_type_counts"]["WARNING"] == 1
    
    def test_save_error_records(self, temp_error_dir):
        handler = ErrorHandler(error_dir=temp_error_dir)
        
        handler.log_error(
            error_type="ERROR",
            message="测试保存错误",
            row_data={"test": "data"},
            row_index=1
        )
        
        handler.save_error_records("test.csv")
        
        error_files = [f for f in os.listdir(temp_error_dir) if f.endswith('.csv')]
        assert len(error_files) > 0
    
    def test_different_error_types(self, temp_error_dir):
        handler = ErrorHandler(error_dir=temp_error_dir)
        
        handler.log_error("CRITICAL", "严重错误")
        handler.log_error("ERROR", "普通错误")
        handler.log_error("WARNING", "警告")
        handler.log_error("INFO", "信息")
        
        summary = handler.get_error_summary()
        
        assert summary["total_errors"] == 4
        assert summary["error_type_counts"]["CRITICAL"] == 1
        assert summary["error_type_counts"]["ERROR"] == 1
        assert summary["error_type_counts"]["WARNING"] == 1
        assert summary["error_type_counts"]["INFO"] == 1
    
    def test_log_error_without_optional_params(self, temp_error_dir):
        handler = ErrorHandler(error_dir=temp_error_dir)
        
        handler.log_error("ERROR", "简单错误信息")
        
        assert handler.error_count == 1
        record = handler.error_records[0]
        assert record["row_index"] is None
        assert record["file_name"] is None
