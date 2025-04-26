"""
投资组合管理代理实现
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import math

from src.agents.base_agent import BaseAgent
from src.roles import create_role_agent
from src.models import AnalysisSignal, StockData, RiskAnalysis, TradingDecision

from camel.messages import BaseMessage


class PortfolioManagerAgent(BaseAgent):
    """投资组合管理代理类"""
    
    def __init__(self, show_reasoning: bool = False, model_name: str = "gemini"):
        """初始化投资组合管理代理
        
        Args:
            show_reasoning: 是否显示推理过程
            model_name: 使用的模型名称 (gemini, openai, qwen)
        """
        role_agent = create_role_agent("portfolio_manager", model_name)
        super().__init__(role_agent, show_reasoning, model_name)
        self.logger = logging.getLogger("PortfolioManagerAgent")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理投资决策
        
        Args:
            data: 包含以下键的字典:
                - stock_data: 股票数据对象
                - technical_analysis: 技术分析结果
                - fundamentals_analysis: 基本面分析结果
                - sentiment_analysis: 情绪分析结果
                - valuation_analysis: 估值分析结果
                - debate_result: 辩论结果
                - risk_analysis: 风险分析结果
                - portfolio: 投资组合信息
                - messages: 处理过程中的消息
                
        Returns:
            Dict[str, Any]: 处理后的数据，包含以下内容:
                - trading_decision: 交易决策
                - messages: 处理过程中的消息
        """
        # 提取各种分析结果和股票数据
        stock_data = data.get("stock_data")
        technical_analysis = data.get("technical_analysis")
        fundamentals_analysis = data.get("fundamentals_analysis")
        sentiment_analysis = data.get("sentiment_analysis")
        valuation_analysis = data.get("valuation_analysis")
        debate_result = data.get("debate_result")
        risk_analysis = data.get("risk_analysis")
        portfolio = data.get("portfolio", {"cash": 100000.0, "stock": 0})
        
        if not stock_data:
            raise ValueError("缺少股票数据")
        
        self.logger.info(f"正在制定投资决策")
        
        try:
            # 提取股票基本信息和最新价格
            ticker = stock_data.ticker
            historical_data = stock_data.historical_data
            latest_price = self._get_latest_price(historical_data)
            
            # 收集所有分析信号
            agent_signals = []
            if technical_analysis:
                agent_signals.append(technical_analysis)
            if fundamentals_analysis:
                agent_signals.append(fundamentals_analysis)
            if sentiment_analysis:
                agent_signals.append(sentiment_analysis)
            if valuation_analysis:
                agent_signals.append(valuation_analysis)
            if debate_result:
                agent_signals.append(debate_result)
                
            # 组织投资决策数据
            decision_data = {
                "ticker": ticker,
                "latest_price": latest_price,
                "portfolio": portfolio,
                "technical_analysis": technical_analysis.dict() if technical_analysis else None,
                "fundamentals_analysis": fundamentals_analysis.dict() if fundamentals_analysis else None,
                "sentiment_analysis": sentiment_analysis.dict() if sentiment_analysis else None,
                "valuation_analysis": valuation_analysis.dict() if valuation_analysis else None,
                "debate_result": debate_result.dict() if debate_result else None,
                "risk_analysis": risk_analysis.dict() if risk_analysis else None
            }
            
            # 使用代理处理数据分析请求
            prompt = f"""请作为投资组合经理，对股票 {ticker} 制定最终的投资决策。
                综合考虑以下因素:
                1. 各类分析师的交易信号
                2. 辩论结果
                3. 风险分析
                4. 当前投资组合状况
                5. 最新市场价格
                
                请给出明确的交易行动（buy/sell/hold）、交易数量和详细理由。
                最新价格: {latest_price}元/股
                
                返回格式为JSON:
                {{
                    "action": "buy/sell/hold",
                    "quantity": 数量,
                    "confidence": 0.8,
                    "reasoning": "投资决策详细理由..."
                }}
                """
                
            analysis_result = self._process_data_with_agent(prompt, decision_data)
            
            # 创建交易决策
            trading_decision = self._create_trading_decision(analysis_result, agent_signals)
            
            # 返回处理结果
            return {
                "trading_decision": trading_decision,
                "messages": []
            }
            
        except Exception as e:
            self.logger.error(f"制定投资决策过程中发生错误: {str(e)}")
            
            # 返回默认交易决策
            default_decision = TradingDecision(
                action="hold",
                quantity=0,
                confidence=0.5,
                agent_signals=[],
                reasoning="决策过程中发生错误，默认保持不变"
            )
            
            return {
                "trading_decision": default_decision,
                "messages": []
            }
    
    def _get_latest_price(self, historical_data: Dict[str, Any]) -> float:
        """获取最新价格
        
        Args:
            historical_data: 历史数据
            
        Returns:
            float: 最新价格
        """
        try:
            # 假设历史数据中有'close'字段，并且是按时间顺序排列的
            if isinstance(historical_data, list) and len(historical_data) > 0:
                return historical_data[-1].get("close", 0.0)
            elif isinstance(historical_data, dict) and "close" in historical_data:
                if isinstance(historical_data["close"], list):
                    return historical_data["close"][-1]
                return historical_data["close"]
        except Exception as e:
            self.logger.error(f"获取最新价格时发生错误: {str(e)}")
        
        return 0.0
            
    def _create_trading_decision(self, analysis_result: Dict[str, Any], agent_signals: List[AnalysisSignal]) -> TradingDecision:
        """创建交易决策
        
        Args:
            analysis_result: 分析结果
            agent_signals: 分析师信号列表
            
        Returns:
            TradingDecision: 交易决策
        """
        action = analysis_result.get("action", "hold")
        quantity = analysis_result.get("quantity", 0)
        confidence = analysis_result.get("confidence", 0.5)
        reasoning = analysis_result.get("reasoning", "未提供决策理由")
        
        # 确保数量是整数
        if not isinstance(quantity, int):
            try:
                quantity = int(quantity)
            except:
                quantity = 0
                
        # 确保数量非负
        quantity = max(0, quantity)
        
        return TradingDecision(
            action=action,
            quantity=quantity,
            confidence=confidence,
            agent_signals=agent_signals,
            reasoning=reasoning
        )
    
    def _process_data_with_agent(self, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """使用代理处理数据分析请求
        
        Args:
            prompt: 分析提示
            data: 包含各种分析数据
            
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
                "action": "hold",
                "quantity": 0,
                "confidence": 0.5,
                "reasoning": "无法解析投资决策，默认保持不变"
            }
            
        return result 