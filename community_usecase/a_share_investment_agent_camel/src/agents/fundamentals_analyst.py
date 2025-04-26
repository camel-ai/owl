"""
基本面分析代理实现
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from src.agents.base_agent import BaseAgent
from src.roles import create_role_agent
from src.models import AnalysisSignal, StockData

from camel.messages import BaseMessage


class FundamentalsAnalystAgent(BaseAgent):
    """基本面分析代理类"""
    
    def __init__(self, show_reasoning: bool = False, model_name: str = "gemini"):
        """初始化基本面分析代理
        
        Args:
            show_reasoning: 是否显示推理过程
            model_name: 使用的模型名称 (gemini, openai, qwen)
        """
        role_agent = create_role_agent("fundamentals_analyst", model_name)
        super().__init__(role_agent, show_reasoning, model_name)
        self.logger = logging.getLogger("FundamentalsAnalystAgent")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理基本面分析
        
        Args:
            data: 包含以下键的字典:
                - stock_data: 股票数据对象
                - messages: 处理过程中的消息
                
        Returns:
            Dict[str, Any]: 处理后的数据，包含以下内容:
                - fundamentals_analysis: 基本面分析信号
                - messages: 处理过程中的消息
        """
        # 提取股票数据
        stock_data = data.get("stock_data")
        if not stock_data:
            raise ValueError("缺少股票数据")
        
        self.logger.info(f"正在进行基本面分析")
        
        try:
            # 提取基本面数据和历史数据
            fundamental_data = stock_data.fundamental_data
            historical_data = stock_data.historical_data
            
            # 使用代理处理数据分析请求
            prompt = f"""请对以下股票的基本面数据进行分析，给出明确的交易信号（bullish/bearish/neutral）。
                分析以下方面:
                1. 财务指标评估（净利润、毛利率、ROE等）
                2. 收入和盈利增长趋势
                3. 估值水平（市盈率、市净率等）
                4. 财务健康状况（资产负债率、流动性等）
                5. 行业地位与竞争优势
                
                请给出明确的交易信号、置信度(0-1)和详细理由。
                返回格式为JSON:
                {{
                    "signal": "bullish/bearish/neutral",
                    "confidence": 0.7,
                    "reasoning": "分析理由...",
                    "key_financials": ["指标1", "指标2"]
                }}
                """
                
            analysis_result = self._process_data_with_agent(prompt, {
                "fundamental_data": fundamental_data,
                "historical_data": historical_data
            })
            
            # 创建基本面分析信号
            fundamentals_analysis = self._create_fundamentals_signal(analysis_result, stock_data)
            
            # 返回处理结果
            return {
                "fundamentals_analysis": fundamentals_analysis,
                "messages": []
            }
            
        except Exception as e:
            self.logger.error(f"基本面分析过程中发生错误: {str(e)}")
            
            # 返回默认分析结果
            default_signal = AnalysisSignal(
                agent="基本面分析师",
                signal="neutral",
                confidence=0.5,
                reasoning="分析过程中发生错误，返回中性信号"
            )
            
            return {
                "fundamentals_analysis": default_signal,
                "messages": []
            }
            
    def _create_fundamentals_signal(self, analysis_result: Dict[str, Any], stock_data: StockData) -> AnalysisSignal:
        """创建基本面分析信号
        
        Args:
            analysis_result: 分析结果
            stock_data: 股票数据
            
        Returns:
            AnalysisSignal: 分析信号
        """
        signal = analysis_result.get("signal", "neutral")
        confidence = analysis_result.get("confidence", 0.5)
        reasoning = analysis_result.get("reasoning", "未提供分析理由")
        key_financials = analysis_result.get("key_financials", [])
        
        details = {
            "ticker": stock_data.ticker,
            "key_financials": key_financials,
        }
        
        return AnalysisSignal(
            agent="基本面分析师",
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
                "key_financials": []
            }
            
        return result 