"""
技术分析代理实现
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import json

from src.agents.base_agent import BaseAgent
from src.roles import create_role_agent
from src.models import StockData, AnalysisSignal

from camel.messages import BaseMessage


class TechnicalAnalystAgent(BaseAgent):
    """技术分析代理类"""
    
    def __init__(self, show_reasoning: bool = False, model_name: str = "gemini"):
        """初始化技术分析代理
        
        Args:
            show_reasoning: 是否显示推理过程
            model_name: 使用的模型名称 (gemini, openai, qwen)
        """
        role_agent = create_role_agent("technical_analyst", model_name)
        super().__init__(role_agent, show_reasoning, model_name)
        self.logger = logging.getLogger("TechnicalAnalystAgent")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理技术分析
        
        Args:
            data: 包含以下键的字典:
                - stock_data: 股票数据对象
                - messages: 处理过程中的消息
                
        Returns:
            Dict[str, Any]: 处理后的数据，包含以下内容:
                - technical_analysis: 技术分析信号
                - messages: 处理过程中的消息
        """
        # 提取股票数据
        stock_data = data.get("stock_data")
        if not stock_data:
            raise ValueError("缺少股票数据")
        
        self.logger.info(f"正在进行技术分析")
        
        try:
            # 提取技术指标
            technical_indicators = stock_data.technical_indicators
            historical_data = stock_data.historical_data
            
            # 使用代理处理数据分析请求
            prompt = f"""请对以下股票的技术指标进行分析，给出明确的交易信号（bullish/bearish/neutral）。
                分析以下方面:
                1. 趋势指标 (移动平均线, MACD等)
                2. 动量指标 (RSI, 随机指标等)
                3. 波动性指标 (布林带, ATR等)
                4. 量价关系
                5. 支撑位和阻力位
                
                请给出明确的交易信号、置信度(0-1)和详细理由。
                返回格式为JSON:
                {{
                    "signal": "bullish/bearish/neutral",
                    "confidence": 0.7,
                    "reasoning": "分析理由...",
                    "key_indicators": ["指标1", "指标2"]
                }}
                """
                
            analysis_result = self._process_data_with_agent(prompt, {
                "technical_indicators": technical_indicators,
                "historical_data": historical_data
            })
            
            # 创建技术分析信号
            technical_analysis = self._create_technical_signal(analysis_result, stock_data)
            
            # 返回处理结果
            return {
                "technical_analysis": technical_analysis,
                "messages": []
            }
            
        except Exception as e:
            self.logger.error(f"技术分析过程中发生错误: {str(e)}")
            
            # 返回默认分析结果
            default_signal = AnalysisSignal(
                agent="技术分析师",
                signal="neutral",
                confidence=0.5,
                reasoning="分析过程中发生错误，返回中性信号"
            )
            
            return {
                "technical_analysis": default_signal,
                "messages": []
            }
    
    def _prepare_analysis_prompt(self, stock_data: StockData) -> str:
        """准备技术分析提示
        
        Args:
            stock_data: 股票数据对象
            
        Returns:
            str: 技术分析提示
        """
        # 提取技术指标
        technical_indicators = stock_data.technical_indicators
        historical_data = stock_data.historical_data
        
        # 构建提示
        prompt = f"""请对以下股票的技术指标进行分析，给出明确的交易信号（bullish/bearish/neutral）。
            分析以下方面:
            1. 趋势指标 (移动平均线, MACD等)
            2. 动量指标 (RSI, 随机指标等)
            3. 波动性指标 (布林带, ATR等)
            4. 量价关系
            5. 支撑位和阻力位
            
            请给出明确的交易信号、置信度(0-1)和详细理由。
            返回格式为JSON:
            {{
                "signal": "bullish/bearish/neutral",
                "confidence": 0.7,
                "reasoning": "分析理由...",
                "key_indicators": ["指标1", "指标2"]
            }}
            """
        return prompt
    
    def _create_technical_signal(self, result: Dict[str, Any], stock_data: StockData) -> AnalysisSignal:
        """创建技术分析信号
        
        Args:
            result: 分析结果
            stock_data: 股票数据对象
            
        Returns:
            AnalysisSignal: 技术分析信号
        """
        signal = result.get("signal", "neutral")
        confidence = result.get("confidence", 0.5)
        reasoning = result.get("reasoning", "")
        key_indicators = result.get("key_indicators", [])
        
        return AnalysisSignal(
            agent="Technical Analysis",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            details={
                "key_indicators": key_indicators
            }
        )
    
    def _process_data_with_agent(self, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """使用代理处理数据分析请求
        
        Args:
            prompt: 分析提示
            data: 包含技术指标和历史数据的数据
            
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
                "key_indicators": []
            }
            
        return result 