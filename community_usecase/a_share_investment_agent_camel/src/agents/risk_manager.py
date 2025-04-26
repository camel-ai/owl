"""
风险管理代理实现
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from src.agents.base_agent import BaseAgent
from src.roles import create_role_agent
from src.models import RiskAnalysis, StockData, Portfolio

from camel.messages import BaseMessage


class RiskManagerAgent(BaseAgent):
    """风险管理代理类"""
    
    def __init__(self, show_reasoning: bool = False, model_name: str = "gemini"):
        """初始化风险管理代理
        
        Args:
            show_reasoning: 是否显示推理过程
            model_name: 使用的模型名称 (gemini, openai, qwen)
        """
        role_agent = create_role_agent("risk_manager", model_name)
        super().__init__(role_agent, show_reasoning, model_name)
        self.logger = logging.getLogger("RiskManagerAgent")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理风险评估
        
        Args:
            data: 包含以下键的字典:
                - stock_data: 股票数据对象
                - debate_result: 辩论结果
                - portfolio: 投资组合信息
                - messages: 处理过程中的消息
                
        Returns:
            Dict[str, Any]: 处理后的数据，包含以下内容:
                - risk_analysis: 风险分析结果
                - messages: 处理过程中的消息
        """
        # 提取股票数据和辩论结果
        stock_data = data.get("stock_data")
        debate_result = data.get("debate_result")
        portfolio = data.get("portfolio")
        
        if not stock_data:
            raise ValueError("缺少股票数据")
        
        if not portfolio:
            portfolio = {"cash": 100000.0, "stock": 0}
            
        self.logger.info(f"正在进行风险评估")
        
        try:
            # 提取股票基本信息和历史数据
            ticker = stock_data.ticker
            historical_data = stock_data.historical_data
            
            # 组织风险评估数据
            risk_data = {
                "ticker": ticker,
                "historical_data": historical_data,
                "debate_result": debate_result.dict() if debate_result else None,
                "portfolio": portfolio
            }
            
            # 使用代理处理数据分析请求
            prompt = f"""请作为风险管理经理，评估投资股票 {ticker} 的风险水平，并提供风险管理建议。
                分析以下方面:
                1. 投资组合风险指标（波动率、最大回撤等）
                2. 市场和特定股票的风险水平
                3. 适当的持仓限制
                4. 止损水平建议
                5. 风险分散策略
                
                请根据分析提供详细的风险管理建议。
                返回格式为JSON:
                {{
                    "max_position_size": 0.2, // 建议最大持仓比例
                    "volatility": 0.15, // 预估股票波动率
                    "risk_score": 0.7, // 0-1之间的风险分数
                    "max_drawdown": 0.25, // 预估最大回撤
                    "suggested_position_size": 0.15, // 建议持仓比例
                    "reasoning": "风险评估理由..."
                }}
                """
                
            analysis_result = self._process_data_with_agent(prompt, risk_data)
            
            # 创建风险分析结果
            risk_analysis = self._create_risk_analysis(analysis_result)
            
            # 返回处理结果
            return {
                "risk_analysis": risk_analysis,
                "messages": []
            }
            
        except Exception as e:
            self.logger.error(f"风险评估过程中发生错误: {str(e)}")
            
            # 返回默认风险分析
            default_analysis = RiskAnalysis(
                max_position_size=0.1,
                volatility=0.2,
                risk_score=0.5,
                max_drawdown=0.2,
                suggested_position_size=0.05,
                reasoning="风险评估过程中发生错误，使用保守默认值"
            )
            
            return {
                "risk_analysis": default_analysis,
                "messages": []
            }
            
    def _create_risk_analysis(self, analysis_result: Dict[str, Any]) -> RiskAnalysis:
        """创建风险分析结果
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            RiskAnalysis: 风险分析结果
        """
        max_position_size = analysis_result.get("max_position_size", 0.1)
        volatility = analysis_result.get("volatility", 0.2)
        risk_score = analysis_result.get("risk_score", 0.5)
        max_drawdown = analysis_result.get("max_drawdown", 0.2)
        suggested_position_size = analysis_result.get("suggested_position_size", 0.05)
        reasoning = analysis_result.get("reasoning", "未提供风险评估理由")
        
        return RiskAnalysis(
            max_position_size=max_position_size,
            volatility=volatility,
            risk_score=risk_score,
            max_drawdown=max_drawdown,
            suggested_position_size=suggested_position_size,
            reasoning=reasoning
        )
    
    def _process_data_with_agent(self, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """使用代理处理数据分析请求
        
        Args:
            prompt: 分析提示
            data: 包含风险评估相关数据
            
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
                "max_position_size": 0.1,
                "volatility": 0.2,
                "risk_score": 0.5,
                "max_drawdown": 0.2,
                "suggested_position_size": 0.05,
                "reasoning": "无法解析风险分析结果，使用保守默认值"
            }
            
        return result 