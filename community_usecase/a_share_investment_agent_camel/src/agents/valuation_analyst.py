"""
估值分析代理实现
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from src.agents.base_agent import BaseAgent
from src.roles import create_role_agent
from src.models import AnalysisSignal, StockData

from camel.messages import BaseMessage


class ValuationAnalystAgent(BaseAgent):
    """估值分析代理类"""
    
    def __init__(self, show_reasoning: bool = False, model_name: str = "gemini"):
        """初始化估值分析代理
        
        Args:
            show_reasoning: 是否显示推理过程
            model_name: 使用的模型名称 (gemini, openai, qwen)
        """
        role_agent = create_role_agent("valuation_analyst", model_name)
        super().__init__(role_agent, show_reasoning, model_name)
        self.logger = logging.getLogger("ValuationAnalystAgent")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理估值分析
        
        Args:
            data: 包含以下键的字典:
                - stock_data: 股票数据对象
                - fundamentals_analysis: 基本面分析结果
                - messages: 处理过程中的消息
                
        Returns:
            Dict[str, Any]: 处理后的数据，包含以下内容:
                - valuation_analysis: 估值分析信号
                - messages: 处理过程中的消息
        """
        # 提取股票数据和基本面分析
        stock_data = data.get("stock_data")
        fundamentals_analysis = data.get("fundamentals_analysis")
        
        if not stock_data:
            raise ValueError("缺少股票数据")
        
        self.logger.info(f"正在进行估值分析")
        
        try:
            # 提取基本面数据和历史数据
            fundamental_data = stock_data.fundamental_data
            historical_data = stock_data.historical_data
            
            # 使用代理处理数据分析请求
            prompt = f"""请对以下股票进行估值分析，给出明确的交易信号（bullish/bearish/neutral）。
                分析以下方面:
                1. 当前市场估值（如PE、PB、PS等）
                2. 估值相对于历史水平
                3. 估值相对于行业平均水平
                4. 使用不同估值模型（如DCF、相对估值法）
                5. 内在价值与当前市场价格的比较
                
                请给出明确的交易信号、置信度(0-1)和详细理由。
                返回格式为JSON:
                {{
                    "signal": "bullish/bearish/neutral",
                    "confidence": 0.7,
                    "reasoning": "分析理由...",
                    "fair_value": 数值,
                    "key_metrics": ["指标1", "指标2"]
                }}
                """
                
            analysis_data = {
                "fundamental_data": fundamental_data,
                "historical_data": historical_data
            }
            
            # 如果有基本面分析结果，添加到分析数据中
            if fundamentals_analysis:
                analysis_data["fundamentals_analysis"] = fundamentals_analysis.dict()
                
            analysis_result = self._process_data_with_agent(prompt, analysis_data)
            
            # 创建估值分析信号
            valuation_analysis = self._create_valuation_signal(analysis_result, stock_data)
            
            # 返回处理结果
            return {
                "valuation_analysis": valuation_analysis,
                "messages": []
            }
            
        except Exception as e:
            self.logger.error(f"估值分析过程中发生错误: {str(e)}")
            
            # 返回默认分析结果
            default_signal = AnalysisSignal(
                agent="估值分析师",
                signal="neutral",
                confidence=0.5,
                reasoning="分析过程中发生错误，返回中性信号"
            )
            
            return {
                "valuation_analysis": default_signal,
                "messages": []
            }
            
    def _create_valuation_signal(self, analysis_result: Dict[str, Any], stock_data: StockData) -> AnalysisSignal:
        """创建估值分析信号
        
        Args:
            analysis_result: 分析结果
            stock_data: 股票数据
            
        Returns:
            AnalysisSignal: 分析信号
        """
        signal = analysis_result.get("signal", "neutral")
        confidence = analysis_result.get("confidence", 0.5)
        reasoning = analysis_result.get("reasoning", "未提供分析理由")
        fair_value = analysis_result.get("fair_value", 0)
        key_metrics = analysis_result.get("key_metrics", [])
        
        details = {
            "ticker": stock_data.ticker,
            "fair_value": fair_value,
            "key_metrics": key_metrics,
        }
        
        return AnalysisSignal(
            agent="估值分析师",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            details=details
        )
    
    def _process_data_with_agent(self, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """使用代理处理数据分析请求
        
        Args:
            prompt: 分析提示
            data: 包含基本面数据和历史数据的数据
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        # 格式化数据
        data_str = self.format_data(data)
        
        # 创建完整提示
        full_prompt = f"""{prompt}

数据:
{data_str}

请以JSON格式返回结果。
"""
        # 发送到Camel代理进行分析
        human_message = self.generate_human_message(content=full_prompt)
        response = self.agent.step(human_message)
        self.log_message(response.msgs[0])
        
        # 解析结果
        result = self.parse_json_response(response.msgs[0].content)
        
        # 如果解析结果为空，使用默认值
        if not result:
            result = {
                "signal": "neutral",
                "confidence": 0.5,
                "reasoning": "无法解析分析结果",
                "fair_value": 0,
                "key_metrics": []
            }
            
        return result 