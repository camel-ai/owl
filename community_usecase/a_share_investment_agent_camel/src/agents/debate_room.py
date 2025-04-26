"""
辩论室代理实现
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from src.agents.base_agent import BaseAgent
from src.roles import create_role_agent
from src.models import AnalysisSignal, StockData, ResearchReport

from camel.messages import BaseMessage


class DebateRoomAgent(BaseAgent):
    """辩论室代理类"""
    
    def __init__(self, show_reasoning: bool = False, model_name: str = "gemini"):
        """初始化辩论室代理
        
        Args:
            show_reasoning: 是否显示推理过程
            model_name: 使用的模型名称 (gemini, openai, qwen)
        """
        role_agent = create_role_agent("debate_room", model_name)
        super().__init__(role_agent, show_reasoning, model_name)
        self.logger = logging.getLogger("DebateRoomAgent")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理多空观点辩论
        
        Args:
            data: 包含以下键的字典:
                - stock_data: 股票数据对象
                - bull_research: 多头研究报告
                - bear_research: 空头研究报告
                - messages: 处理过程中的消息
                
        Returns:
            Dict[str, Any]: 处理后的数据，包含以下内容:
                - debate_result: 辩论结果信号
                - messages: 处理过程中的消息
        """
        # 提取股票数据和研究报告
        stock_data = data.get("stock_data")
        bull_research = data.get("bull_research")
        bear_research = data.get("bear_research")
        
        if not stock_data:
            raise ValueError("缺少股票数据")
        
        if not bull_research or not bear_research:
            raise ValueError("缺少多头或空头研究报告")
        
        self.logger.info(f"正在召开辩论会议")
        
        try:
            # 提取股票基本信息
            ticker = stock_data.ticker
            
            # 组织研究报告数据
            debate_data = {
                "ticker": ticker,
                "bull_research": bull_research.dict(),
                "bear_research": bear_research.dict(),
            }
            
            # 使用代理处理数据分析请求
            prompt = f"""请作为辩论室主持人，整合多头和空头研究员对股票 {ticker} 的观点，形成一个平衡的投资视角。
                任务要求:
                1. 公正评估多头和空头论据的优点和弱点
                2. 识别最具说服力的论点
                3. 权衡不同因素的重要性
                4. 形成综合性的市场观点
                5. 提出平衡的投资建议
                
                请给出明确的交易信号、置信度和详细理由。
                返回格式为JSON:
                {{
                    "signal": "bullish/bearish/neutral",
                    "confidence": 0.7,
                    "reasoning": "辩论总结和推理...",
                    "bull_key_strengths": ["优势1", "优势2"],
                    "bull_key_weaknesses": ["弱点1", "弱点2"],
                    "bear_key_strengths": ["优势1", "优势2"],
                    "bear_key_weaknesses": ["弱点1", "弱点2"],
                    "final_verdict": "最终投资建议..."
                }}
                """
                
            analysis_result = self._process_data_with_agent(prompt, debate_data)
            
            # 创建辩论结果信号
            debate_result = self._create_debate_signal(analysis_result, ticker)
            
            # 返回处理结果
            return {
                "debate_result": debate_result,
                "messages": []
            }
            
        except Exception as e:
            self.logger.error(f"辩论过程中发生错误: {str(e)}")
            
            # 返回默认辩论结果
            default_signal = AnalysisSignal(
                agent="辩论室",
                signal="neutral",
                confidence=0.5,
                reasoning="辩论过程中发生错误，返回中性信号"
            )
            
            return {
                "debate_result": default_signal,
                "messages": []
            }
            
    def _create_debate_signal(self, analysis_result: Dict[str, Any], ticker: str) -> AnalysisSignal:
        """创建辩论结果信号
        
        Args:
            analysis_result: 分析结果
            ticker: 股票代码
            
        Returns:
            AnalysisSignal: 分析信号
        """
        signal = analysis_result.get("signal", "neutral")
        confidence = analysis_result.get("confidence", 0.5)
        reasoning = analysis_result.get("reasoning", "未提供分析理由")
        final_verdict = analysis_result.get("final_verdict", "")
        
        # 整合多空优缺点
        bull_strengths = analysis_result.get("bull_key_strengths", [])
        bull_weaknesses = analysis_result.get("bull_key_weaknesses", [])
        bear_strengths = analysis_result.get("bear_key_strengths", [])
        bear_weaknesses = analysis_result.get("bear_key_weaknesses", [])
        
        details = {
            "ticker": ticker,
            "bull_strengths": bull_strengths,
            "bull_weaknesses": bull_weaknesses,
            "bear_strengths": bear_strengths,
            "bear_weaknesses": bear_weaknesses,
            "final_verdict": final_verdict
        }
        
        return AnalysisSignal(
            agent="辩论室",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            details=details
        )
    
    def _process_data_with_agent(self, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """使用代理处理数据分析请求
        
        Args:
            prompt: 分析提示
            data: 包含多空研究报告的数据
            
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
                "reasoning": "无法解析辩论结果",
                "bull_key_strengths": [],
                "bull_key_weaknesses": [],
                "bear_key_strengths": [],
                "bear_key_weaknesses": [],
                "final_verdict": "由于分析错误，无法给出最终判断"
            }
            
        return result 