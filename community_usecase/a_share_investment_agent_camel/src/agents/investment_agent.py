"""
投资分析代理实现
"""
import logging
from typing import Dict, Any, List, Optional
import json
import re

from src.agents.base_agent import BaseAgent
from src.roles import create_role_agent
from src.models import StockData

from camel.messages import BaseMessage


class InvestmentAgent(BaseAgent):
    """投资分析代理类"""
    
    def __init__(self, show_reasoning: bool = False, model_name: str = "gemini"):
        """初始化投资分析代理
        
        Args:
            show_reasoning: 是否显示推理过程
            model_name: 使用的模型名称 (gemini, openai, qwen)
        """
        role_agent = create_role_agent("investment_analyst", model_name)
        super().__init__(role_agent, show_reasoning, model_name)
        self.logger = logging.getLogger("InvestmentAgent")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理投资分析请求
        
        Args:
            data: 输入数据，包含股票信息
            
        Returns:
            Dict[str, Any]: 投资分析结果
        """
        try:
            # 获取输入数据
            stock_data = data.get("stock_data")
            if not stock_data:
                raise ValueError("缺少股票数据")
            
            ticker = stock_data.ticker
            
            # 获取财务数据
            fundamental_data = stock_data.fundamental_data
            
            # 获取历史数据
            historical_data = fundamental_data.get("historical_data", [])
            financial_trends = fundamental_data.get("trends", {})
            
            # 创建分析提示
            prompt = f"""你是一位专业的投资分析师，请根据以下数据对股票 {ticker} 进行全面的投资分析和推荐：

            1. 基本面分析：
               - 财务状况：分析公司收入、利润、现金流和资产负债情况
               - 增长趋势：评估收入增长、利润增长和ROE变化趋势
               - 估值指标：分析市盈率、市净率等估值指标的合理性
            
            2. 技术面分析：
               - 价格趋势：分析股票价格走势
               - 成交量：评估交易量变化
               - 技术指标：解读主要技术指标
            
            3. 投资建议：
               - 给出明确的投资建议（买入/持有/卖出）
               - 说明理由和风险因素
               - 给出合理的目标价格区间

            4. 风险分析：
               - 列出主要风险因素
               - 给出风险应对建议

            请基于数据给出客观、全面的分析，避免过度乐观或悲观的观点。分析应当深入浅出，使投资者容易理解。
            """
            
            # 构建分析输入
            analysis_input = {
                "ticker": ticker,
                "financial_data": fundamental_data,
                "historical_data": historical_data,
                "financial_trends": financial_trends,
                "technical_indicators": stock_data.technical_indicators,
                "historical_prices": stock_data.historical_data,
                "news": stock_data.news_data
            }
            
            # 使用代理进行分析
            analysis_result = self._process_data_with_agent(prompt, analysis_input)
            
            # 提取投资建议
            recommendation = self._extract_recommendation(analysis_result)
            
            # 返回结果
            return {
                "analysis": analysis_result,
                "recommendation": recommendation,
                "messages": []  # 暂时返回空消息列表
            }
            
        except Exception as e:
            self.logger.error(f"进行投资分析时发生错误: {str(e)}")
            raise e

    def _process_data_with_agent(self, prompt: str, data: Dict[str, Any]) -> str:
        """使用代理处理数据分析请求
        
        Args:
            prompt: 分析提示
            data: 包含基本面数据和历史数据的数据
            
        Returns:
            str: 分析结果文本
        """
        # 格式化数据
        data_str = self.format_data(data)
        
        # 创建完整提示
        full_prompt = f"""{prompt}

数据:
{data_str}

请提供详细的分析报告。
"""
        # 发送到Camel代理进行分析
        human_message = self.generate_human_message(content=full_prompt)
        response = self.agent.step(human_message)
        self.log_message(response.msgs[0])
        
        # 返回结果文本
        return response.msgs[0].content
    
    def generate_human_message(self, content: str) -> BaseMessage:
        """生成人类消息
        
        Args:
            content: 消息内容
            
        Returns:
            BaseMessage: 人类消息对象
        """
        return BaseMessage(role_name="Human", role_type="user", meta_info={}, content=content)
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应
        
        Args:
            response: 响应文本
            
        Returns:
            Dict[str, Any]: 解析后的JSON数据
        """
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试找到可能的JSON对象
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    return {}
            
            # 解析JSON
            return json.loads(json_str)
        except Exception as e:
            self.logger.error(f"解析JSON响应时发生错误: {str(e)}")
            return {}

    def _extract_recommendation(self, analysis: str) -> Dict[str, Any]:
        """从分析结果中提取投资建议
        
        Args:
            analysis: 分析文本
            
        Returns:
            Dict[str, Any]: 投资建议
        """
        try:
            # 使用代理提取关键信息
            prompt = """从以下投资分析报告中提取关键信息，包括：
            1. 投资评级（买入/持有/卖出）
            2. 目标价格区间（如果有）
            3. 主要投资理由（不超过3点）
            4. 主要风险因素（不超过3点）
            
            以JSON格式返回结果，包含以下字段：
            - rating: 投资评级
            - target_price_low: 目标价格下限（如果有）
            - target_price_high: 目标价格上限（如果有）
            - reasons: 投资理由列表
            - risks: 风险因素列表
            
            分析报告：
            """
            
            extraction_result = self._process_data_with_agent(prompt + analysis, {})
            
            # 尝试解析JSON结果
            try:
                import json
                json_match = re.search(r'\{[\s\S]*\}', extraction_result)
                if json_match:
                    json_str = json_match.group(0)
                    recommendation = json.loads(json_str)
                    return recommendation
                else:
                    return {
                        "rating": self._determine_rating(analysis),
                        "target_price_low": 0,
                        "target_price_high": 0,
                        "reasons": [],
                        "risks": []
                    }
            except:
                # 如果解析失败，返回简化结果
                return {
                    "rating": self._determine_rating(analysis),
                    "target_price_low": 0,
                    "target_price_high": 0,
                    "reasons": [],
                    "risks": []
                }
                
        except Exception as e:
            self.logger.error(f"提取投资建议时发生错误: {str(e)}")
            return {
                "rating": "未知",
                "target_price_low": 0,
                "target_price_high": 0,
                "reasons": [],
                "risks": []
            }
    
    def _determine_rating(self, analysis: str) -> str:
        """从分析文本中确定投资评级
        
        Args:
            analysis: 分析文本
            
        Returns:
            str: 投资评级
        """
        analysis_lower = analysis.lower()
        
        if "买入" in analysis or "强烈推荐" in analysis or "buy" in analysis_lower:
            return "买入"
        elif "卖出" in analysis or "sell" in analysis_lower:
            return "卖出"
        elif "持有" in analysis or "观望" in analysis or "hold" in analysis_lower:
            return "持有"
        else:
            return "未知"
            
    def _analyze_financial_trends(self, historical_data: List[Dict[str, Any]], trends: Dict[str, Any]) -> str:
        """分析财务趋势
        
        Args:
            historical_data: 历史财务数据
            trends: 财务趋势数据
            
        Returns:
            str: 财务趋势分析
        """
        if not historical_data or len(historical_data) < 2:
            return "财务数据不足以进行趋势分析。"
        
        analysis = []
        
        # 收入趋势分析
        if "revenue" in trends:
            revenue_trend = trends["revenue"]
            revenue_values = revenue_trend.get("values", [])
            revenue_growth = revenue_trend.get("growth", 0)
            revenue_trend_dir = revenue_trend.get("trend", "未知")
            
            if revenue_values:
                if revenue_growth > 20:
                    analysis.append(f"公司收入呈高速{revenue_trend_dir}趋势，同比增长{revenue_growth:.2f}%，显示出强劲的业务增长。")
                elif revenue_growth > 5:
                    analysis.append(f"公司收入呈稳健{revenue_trend_dir}趋势，同比增长{revenue_growth:.2f}%，业务发展稳定。")
                elif revenue_growth >= 0:
                    analysis.append(f"公司收入略有{revenue_trend_dir}，同比增长{revenue_growth:.2f}%，业务增长放缓。")
                else:
                    analysis.append(f"公司收入呈{revenue_trend_dir}趋势，同比下降{abs(revenue_growth):.2f}%，业务面临挑战。")
        
        # 净利润趋势分析
        if "net_income" in trends:
            income_trend = trends["net_income"]
            income_values = income_trend.get("values", [])
            income_growth = income_trend.get("growth", 0)
            income_trend_dir = income_trend.get("trend", "未知")
            
            if income_values:
                if income_growth > 20:
                    analysis.append(f"公司净利润呈高速{income_trend_dir}趋势，同比增长{income_growth:.2f}%，盈利能力强劲。")
                elif income_growth > 5:
                    analysis.append(f"公司净利润呈稳健{income_trend_dir}趋势，同比增长{income_growth:.2f}%，盈利能力稳定。")
                elif income_growth >= 0:
                    analysis.append(f"公司净利润略有{income_trend_dir}，同比增长{income_growth:.2f}%，盈利增长放缓。")
                else:
                    analysis.append(f"公司净利润呈{income_trend_dir}趋势，同比下降{abs(income_growth):.2f}%，盈利能力受到挑战。")
        
        # ROE趋势分析
        if "roe" in trends:
            roe_trend = trends["roe"]
            roe_values = roe_trend.get("values", [])
            roe_trend_dir = roe_trend.get("trend", "未知")
            
            if roe_values and len(roe_values) > 0:
                latest_roe = roe_values[0]
                if latest_roe > 15:
                    analysis.append(f"公司ROE为{latest_roe:.2f}%，处于较高水平，资本回报率优秀。ROE呈{roe_trend_dir}趋势。")
                elif latest_roe > 10:
                    analysis.append(f"公司ROE为{latest_roe:.2f}%，处于良好水平，资本回报率不错。ROE呈{roe_trend_dir}趋势。")
                elif latest_roe > 5:
                    analysis.append(f"公司ROE为{latest_roe:.2f}%，处于一般水平，资本回报率尚可。ROE呈{roe_trend_dir}趋势。")
                else:
                    analysis.append(f"公司ROE为{latest_roe:.2f}%，处于较低水平，资本回报率不佳。ROE呈{roe_trend_dir}趋势。")
        
        # 季度对比分析
        if len(historical_data) >= 4:
            latest_quarter = historical_data[0]
            year_ago_quarter = None
            
            # 寻找去年同期数据（通常是第4个季度报告）
            if len(historical_data) >= 4:
                year_ago_quarter = historical_data[3]
            
            if latest_quarter and year_ago_quarter:
                latest_revenue = float(latest_quarter["income_statement"]["revenue"])
                latest_net_income = float(latest_quarter["income_statement"]["net_income"])
                
                year_ago_revenue = float(year_ago_quarter["income_statement"]["revenue"])
                year_ago_net_income = float(year_ago_quarter["income_statement"]["net_income"])
                
                # 计算同比增长率
                if year_ago_revenue > 0:
                    yoy_revenue_growth = (latest_revenue - year_ago_revenue) / year_ago_revenue * 100
                    analysis.append(f"同比而言，该季度营收增长{yoy_revenue_growth:.2f}%。")
                
                if year_ago_net_income > 0:
                    yoy_net_income_growth = (latest_net_income - year_ago_net_income) / year_ago_net_income * 100
                    analysis.append(f"同比而言，该季度净利润增长{yoy_net_income_growth:.2f}%。")
        
        return "\n".join(analysis) 