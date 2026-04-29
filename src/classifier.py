import os
import re
from typing import Dict, Any, List, Optional
import yaml


class TransactionClassifier:
    def __init__(self, config_path: Optional[str] = None):
        self.rules: List[Dict[str, Any]] = []
        self.default_category: str = "未分类"
        
        if config_path and os.path.exists(config_path):
            self.load_rules(config_path)
        else:
            self._load_default_rules()
    
    def _load_default_rules(self):
        self.rules = [
            {
                "category": "工资收入",
                "patterns": ["工资", "薪资", "薪水", "代发工资", "薪酬"],
                "amount_condition": {"operator": ">", "value": 0}
            },
            {
                "category": "餐饮美食",
                "patterns": ["餐饮", "美食", "餐厅", "饭店", "餐馆", "星巴克", "咖啡", "奶茶", "KFC", "肯德基", "麦当劳"],
                "amount_condition": None
            },
            {
                "category": "日常消费",
                "patterns": ["超市", "便利店", "沃尔玛", "家乐福", "永辉", "购物"],
                "amount_condition": None
            },
            {
                "category": "交通出行",
                "patterns": ["滴滴", "出行", "打车", "地铁", "公交", "加油", "停车", "过路费", "火车票", "机票", "携程", "飞猪"],
                "amount_condition": None
            },
            {
                "category": "娱乐休闲",
                "patterns": ["电影", "KTV", "游戏", "充值", "会员", "视频网站", "爱奇艺", "腾讯视频", "优酷"],
                "amount_condition": None
            },
            {
                "category": "转账汇款",
                "patterns": ["转账", "汇款", "转给", "来自.*转账", "支付宝.*转账", "微信.*转账"],
                "amount_condition": None
            },
            {
                "category": "投资理财",
                "patterns": ["基金", "股票", "理财", "投资", "债券", "定期", "活期"],
                "amount_condition": None
            },
            {
                "category": "住房相关",
                "patterns": ["房租", "租金", "房贷", "物业", "水电", "燃气", "暖气"],
                "amount_condition": None
            },
            {
                "category": "医疗健康",
                "patterns": ["医院", "药店", "药品", "体检", "挂号", "医保"],
                "amount_condition": None
            },
            {
                "category": "教育学习",
                "patterns": ["培训", "课程", "学费", "书籍", "教育", "学习"],
                "amount_condition": None
            }
        ]
    
    def load_rules(self, config_path: str):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config and 'classification_rules' in config:
                self.rules = config['classification_rules']
            else:
                self._load_default_rules()
                
        except Exception as e:
            print(f"Warning: Failed to load classification rules from {config_path}: {e}")
            self._load_default_rules()
    
    def classify(self, description: str, amount: float = 0) -> str:
        if not description:
            return self.default_category
        
        description = str(description).lower()
        
        for rule in self.rules:
            category = rule.get("category", self.default_category)
            patterns = rule.get("patterns", [])
            amount_condition = rule.get("amount_condition")
            
            match_found = False
            for pattern in patterns:
                if re.search(pattern.lower(), description):
                    match_found = True
                    break
            
            if match_found:
                if amount_condition:
                    operator = amount_condition.get("operator")
                    value = amount_condition.get("value", 0)
                    
                    if operator == ">" and not (amount > value):
                        continue
                    elif operator == ">=" and not (amount >= value):
                        continue
                    elif operator == "<" and not (amount < value):
                        continue
                    elif operator == "<=" and not (amount <= value):
                        continue
                    elif operator == "==" and not (amount == value):
                        continue
                
                return category
        
        return self.default_category
    
    def add_rule(self, category: str, patterns: List[str], 
                 amount_condition: Optional[Dict[str, Any]] = None):
        self.rules.insert(0, {
            "category": category,
            "patterns": patterns,
            "amount_condition": amount_condition
        })
    
    def get_categories(self) -> List[str]:
        categories = set()
        for rule in self.rules:
            categories.add(rule.get("category", self.default_category))
        categories.add(self.default_category)
        return sorted(list(categories))
