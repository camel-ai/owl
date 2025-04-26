"""
多头研究员代理实现
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from src.agents.base_agent import BaseAgent
from src.roles import create_role_agent
from src.models import AnalysisSignal, StockData, ResearchReport

from camel.messages import BaseMessage


class ResearcherBullAgent(BaseAgent):
    """多头研究员代理类"""
    
    def __init__(self, show_reasoning: bool = False, model_name: str = "gemini"):
        """初始化多头研究员代理
        
        Args:
            show_reasoning: 是否显示推理过程
            model_name: 使用的模型名称 (gemini, openai, qwen)
        """
        role_agent = create_role_agent("researcher_bull", model_name)
        super().__init__(role_agent, show_reasoning, model_name)
        self.logger = logging.getLogger("ResearcherBullAgent")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理多头研究报告生成
        
        Args:
            data: 包含以下键的字典:
                - stock_data: 股票数据对象
                - technical_analysis: 技术分析结果
                - fundamentals_analysis: 基本面分析结果
                - sentiment_analysis: 情绪分析结果
                - valuation_analysis: 估值分析结果
                - messages: 处理过程中的消息
                
        Returns:
            Dict[str, Any]: 处理后的数据，包含以下内容:
                - bull_research: 多头研究报告
                - messages: 处理过程中的消息
        """
        # 提取股票数据和各类分析结果
        stock_data = data.get("stock_data")
        technical_analysis = data.get("technical_analysis")
        fundamentals_analysis = data.get("fundamentals_analysis")
        sentiment_analysis = data.get("sentiment_analysis")
        valuation_analysis = data.get("valuation_analysis")
        
        if not stock_data:
            raise ValueError("缺少股票数据")
        
        self.logger.info(f"正在生成多头研究报告")
        
        try:
            # 提取股票基本信息
            ticker = stock_data.ticker
            
            # 组织各种分析结果
            analysis_data = {
                "ticker": ticker,
                "technical_analysis": technical_analysis.dict() if technical_analysis else None,
                "fundamentals_analysis": fundamentals_analysis.dict() if fundamentals_analysis else None,
                "sentiment_analysis": sentiment_analysis.dict() if sentiment_analysis else None,
                "valuation_analysis": valuation_analysis.dict() if valuation_analysis else None
            }
            
            # 使用代理处理数据分析请求
            prompt = f"""请作为持有看多观点的研究员，寻找支持买入股票 {ticker} 的最有力证据和论据。
                重点关注以下方面:
                1. 技术分析中的看涨信号
                2. 基本面分析中的积极因素
                3. 市场情绪分析中的乐观迹象
                4. 估值分析中的低估证据
                5. 可能被市场忽视的积极因素
                
                请提供一份全面的看多研究报告，以JSON格式返回:
                {{
                    "key_points": ["关键点1", "关键点2", ...],
                    "confidence": 0.8,
                    "technical_summary": "技术分析总结...",
                    "fundamental_summary": "基本面分析总结...",
                    "sentiment_summary": "情绪分析总结...",
                    "valuation_summary": "估值分析总结...",
                    "reasoning": "整体推理过程和看多理由..."
                }}
                """
                
            analysis_result = self._process_data_with_agent(prompt, analysis_data)
            
            # 创建研究报告
            bull_research = self._create_research_report(analysis_result, ticker)
            
            # 返回处理结果
            return {
                "bull_research": bull_research,
                "messages": []
            }
            
        except Exception as e:
            self.logger.error(f"生成多头研究报告过程中发生错误: {str(e)}")
            
            # 返回默认研究报告
            default_report = ResearchReport(
                stance="bullish",
                key_points=["数据不足以支持详细分析"],
                confidence=0.5,
                reasoning="处理过程中发生错误，无法生成完整研究报告"
            )
            
            return {
                "bull_research": default_report,
                "messages": []
            }
            
    def _create_research_report(self, analysis_result: Dict[str, Any], ticker: str) -> ResearchReport:
        """创建研究报告
        
        Args:
            analysis_result: 分析结果
            ticker: 股票代码
            
        Returns:
            ResearchReport: 研究报告
        """
        key_points = analysis_result.get("key_points", ["无关键点"])
        confidence = analysis_result.get("confidence", 0.5)
        technical_summary = analysis_result.get("technical_summary")
        fundamental_summary = analysis_result.get("fundamental_summary")
        sentiment_summary = analysis_result.get("sentiment_summary")
        valuation_summary = analysis_result.get("valuation_summary")
        reasoning = analysis_result.get("reasoning", "未提供分析理由")
        
        return ResearchReport(
            stance="bullish",
            key_points=key_points,
            confidence=confidence,
            technical_summary=technical_summary,
            fundamental_summary=fundamental_summary,
            sentiment_summary=sentiment_summary,
            valuation_summary=valuation_summary,
            reasoning=reasoning
        )
    
    def _process_data_with_agent(self, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """使用代理处理数据分析请求
        
        Args:
            prompt: 分析提示
            data: 包含各类分析结果的数据
            
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
                "key_points": ["无法解析分析结果"],
                "confidence": 0.5,
                "technical_summary": "无法获取技术分析总结",
                "fundamental_summary": "无法获取基本面分析总结",
                "sentiment_summary": "无法获取情绪分析总结",
                "valuation_summary": "无法获取估值分析总结",
                "reasoning": "无法解析多头研究报告"
            }
            
        return result 