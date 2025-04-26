"""
数据模型定义
"""
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
import json


class StockData(BaseModel):
    """股票数据模型"""
    ticker: str
    historical_data: Dict[str, Any] = Field(default_factory=dict)
    fundamental_data: Dict[str, Any] = Field(default_factory=dict)
    technical_indicators: Dict[str, Any] = Field(default_factory=dict)
    news_data: Dict[str, Any] = Field(default_factory=dict)
    
    
class AnalysisSignal(BaseModel):
    """分析信号"""
    agent: str
    signal: str  # bullish, bearish, neutral
    confidence: float  # 0.0 - 1.0
    reasoning: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class DateTimeEncoder(json.JSONEncoder):
    """处理datetime的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class TradingDecision(BaseModel):
    """交易决策"""
    action: str  # buy, sell, hold
    quantity: int
    confidence: float
    agent_signals: List[AnalysisSignal]
    reasoning: str
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now()
        super().__init__(**data)
    
    def dict(self):
        """返回字典表示，可JSON序列化"""
        base_dict = super().dict()
        # 转换datetime为ISO格式字符串
        base_dict['timestamp'] = base_dict['timestamp'].isoformat() if base_dict['timestamp'] else None
        return base_dict


class Portfolio(BaseModel):
    """投资组合"""
    cash: float = 100000.0
    stock: int = 0
    stock_value: float = 0.0
    total_value: float = Field(default=0.0)
    holdings: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    def update_total_value(self):
        """更新总价值"""
        self.total_value = self.cash + self.stock_value


class RiskAnalysis(BaseModel):
    """风险分析"""
    max_position_size: float
    volatility: float
    risk_score: float  # 0.0 - 1.0
    max_drawdown: float
    suggested_position_size: float
    reasoning: Optional[str] = None


class ResearchReport(BaseModel):
    """研究报告"""
    stance: str  # bullish, bearish
    key_points: List[str]
    confidence: float
    technical_summary: Optional[str] = None
    fundamental_summary: Optional[str] = None
    sentiment_summary: Optional[str] = None
    valuation_summary: Optional[str] = None
    reasoning: Optional[str] = None 