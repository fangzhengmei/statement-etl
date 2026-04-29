import pytest

from src.classifier import TransactionClassifier


class TestTransactionClassifier:
    def test_classifier_initialization(self):
        classifier = TransactionClassifier()
        assert classifier is not None
        assert len(classifier.rules) > 0
    
    def test_classify_salary(self):
        classifier = TransactionClassifier()
        
        category = classifier.classify("工资发放", 5000.0)
        assert category == "工资收入"
    
    def test_classify_food(self):
        classifier = TransactionClassifier()
        
        category = classifier.classify("星巴克咖啡", 50.0)
        assert category == "餐饮美食"
    
    def test_classify_transport(self):
        classifier = TransactionClassifier()
        
        category = classifier.classify("滴滴出行", 30.0)
        assert category == "交通出行"
    
    def test_classify_transfer(self):
        classifier = TransactionClassifier()
        
        category = classifier.classify("转账给张三", 1000.0)
        assert category == "转账汇款"
    
    def test_classify_uncategorized(self):
        classifier = TransactionClassifier()
        
        category = classifier.classify("未知交易类型", 100.0)
        assert category == "未分类"
    
    def test_classify_case_insensitive(self):
        classifier = TransactionClassifier()
        
        category1 = classifier.classify("星巴克", 50.0)
        category2 = classifier.classify("星巴克咖啡", 50.0)
        
        assert category1 == category2
        assert category1 == "餐饮美食"
    
    def test_add_rule(self):
        classifier = TransactionClassifier()
        
        classifier.add_rule(
            "自定义分类",
            ["自定义关键词1", "自定义关键词2"],
            {"operator": ">", "value": 100}
        )
        
        category = classifier.classify("自定义关键词1交易", 200.0)
        assert category == "自定义分类"
    
    def test_get_categories(self):
        classifier = TransactionClassifier()
        
        categories = classifier.get_categories()
        
        assert len(categories) > 0
        assert "未分类" in categories
        assert "工资收入" in categories
    
    def test_amount_condition(self):
        classifier = TransactionClassifier()
        
        classifier.add_rule(
            "大额交易",
            ["转账"],
            {"operator": ">", "value": 10000}
        )
        
        small_transfer = classifier.classify("转账给朋友", 5000.0)
        large_transfer = classifier.classify("转账大额", 20000.0)
        
        assert small_transfer == "转账汇款"
        assert large_transfer == "大额交易"
    
    def test_classify_without_description(self):
        classifier = TransactionClassifier()
        
        category = classifier.classify("", 100.0)
        assert category == "未分类"
        
        category = classifier.classify(None, 100.0)
        assert category == "未分类"
