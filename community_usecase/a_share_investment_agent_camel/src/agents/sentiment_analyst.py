"""
情绪分析代理实现
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from src.agents.base_agent import BaseAgent
from src.roles import create_role_agent
from src.models import AnalysisSignal, StockData

from camel.messages import BaseMessage


class SentimentAnalystAgent(BaseAgent):
    """情绪分析代理类"""
    
    def __init__(self, show_reasoning: bool = False, model_name: str = "gemini"):
        """初始化情绪分析代理
        
        Args:
            show_reasoning: 是否显示推理过程
            model_name: 使用的模型名称 (gemini, openai, qwen)
        """
        role_agent = create_role_agent("sentiment_analyst", model_name)
        super().__init__(role_agent, show_reasoning, model_name)
        self.logger = logging.getLogger("SentimentAnalystAgent")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理情绪分析
        
        Args:
            data: 包含以下键的字典:
                - stock_data: 股票数据对象
                - messages: 处理过程中的消息
                
        Returns:
            Dict[str, Any]: 处理后的数据，包含以下内容:
                - sentiment_analysis: 情绪分析信号
                - messages: 处理过程中的消息
        """
        # 提取股票数据
        stock_data = data.get("stock_data")
        
        if not stock_data:
            raise ValueError("缺少股票数据")
        
        self.logger.info(f"正在进行情绪分析")
        
        try:
            # 提取股票基本信息和新闻数据
            ticker = stock_data.ticker
            news_data = stock_data.news_data
            
            # 使用代理处理数据分析请求
            prompt = f"""请对以下与股票相关的新闻和社交媒体数据进行分析，给出明确的市场情绪信号（bullish/bearish/neutral）。
                分析以下方面:
                1. 整体市场情绪（积极、中性或消极）
                2. 重要事件或新闻的影响
                3. 机构投资者和分析师观点
                4. 社交媒体讨论的热度和倾向性
                5. 情绪变化趋势
                
                请给出明确的交易信号、置信度(0-1)和详细理由。
                返回格式为JSON:
                {{
                    "signal": "bullish/bearish/neutral",
                    "confidence": 0.7,
                    "reasoning": "分析理由...",
                    "key_events": ["事件1", "事件2"]
                }}
                """
                
            analysis_result = self._process_data_with_agent(prompt, {
                "ticker": ticker,
                "news_data": news_data
            })
            
            # 创建情绪分析信号
            sentiment_analysis = self._create_sentiment_signal(analysis_result, stock_data)
            
            # 返回处理结果
            return {
                "sentiment_analysis": sentiment_analysis,
                "messages": []
            }
            
        except Exception as e:
            self.logger.error(f"情绪分析过程中发生错误: {str(e)}")
            
            # 返回默认分析结果
            default_signal = AnalysisSignal(
                agent="情绪分析师",
                signal="neutral",
                confidence=0.5,
                reasoning="分析过程中发生错误，返回中性信号"
            )
            
            return {
                "sentiment_analysis": default_signal,
                "messages": []
            }
            
    def _create_sentiment_signal(self, analysis_result: Dict[str, Any], stock_data: StockData) -> AnalysisSignal:
        """创建情绪分析信号
        
        Args:
            analysis_result: 分析结果
            stock_data: 股票数据
            
        Returns:
            AnalysisSignal: 分析信号
        """
        signal = analysis_result.get("signal", "neutral")
        confidence = analysis_result.get("confidence", 0.5)
        reasoning = analysis_result.get("reasoning", "未提供分析理由")
        key_events = analysis_result.get("key_events", [])
        
        details = {
            "ticker": stock_data.ticker,
            "key_events": key_events,
        }
        
        return AnalysisSignal(
            agent="情绪分析师",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            details=details
        )
    
    def _process_data_with_agent(self, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """使用代理处理数据分析请求
        
        Args:
            prompt: 分析提示
            data: 包含新闻数据的字典
            
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
                "key_events": []
            }
            
        return result 