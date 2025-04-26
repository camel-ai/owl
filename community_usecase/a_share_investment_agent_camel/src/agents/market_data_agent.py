"""
市场数据分析代理实现
"""
import os
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

from src.agents.base_agent import BaseAgent
from src.roles import create_role_agent
from src.models import StockData

from camel.messages import BaseMessage, OpenAIUserMessage, OpenAIAssistantMessage


class MarketDataAgent(BaseAgent):
    """市场数据分析代理类"""
    
    def __init__(self, show_reasoning: bool = False, model_name: str = "gemini"):
        """初始化市场数据分析代理
        
        Args:
            show_reasoning: 是否显示推理过程
            model_name: 使用的模型名称 (gemini, openai, qwen)
        """
        role_agent = create_role_agent("market_data_analyst", model_name)
        super().__init__(role_agent, show_reasoning, model_name)
        self.logger = logging.getLogger("MarketDataAgent")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理市场数据获取和预处理
        
        Args:
            data: 包含以下键的字典:
                - ticker: 股票代码
                - start_date: 开始日期
                - end_date: 结束日期
                - num_of_news: 新闻数量
                
        Returns:
            Dict[str, Any]: 处理后的数据，包含以下内容:
                - stock_data: 股票数据对象
                - messages: 处理过程中的消息
        """
        # 提取参数
        ticker = data.get("ticker")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        num_of_news = data.get("num_of_news", 5)
        
        if not ticker:
            raise ValueError("缺少股票代码")
        
        self.logger.info(f"正在获取 {ticker} 的市场数据")
        
        try:
            # 获取历史价格数据
            historical_data = self._get_historical_data(ticker, start_date, end_date)
            
            # 计算技术指标
            technical_indicators = self._calculate_technical_indicators(historical_data)
            
            # 获取财务数据
            fundamental_data = self._get_financial_data(ticker)
            
            # 获取新闻数据
            news_data = self._get_news_data(ticker, num_of_news)
            
            # 创建股票数据对象
            stock_data = StockData(
                ticker=ticker,
                historical_data=historical_data,
                technical_indicators=technical_indicators,
                fundamental_data=fundamental_data,
                news_data=news_data
            )
            
            # 使用代理处理数据分析请求
            prompt = f"""请分析以下关于股票 {ticker} 的市场数据，识别重要趋势和关键指标表现。
                提供以下方面的见解:
                1. 价格走势概要
                2. 成交量分析
                3. 主要技术指标分析（RSI、MACD、布林带）
                4. 关键支撑和阻力位
                5. 市场趋势和整体判断"""
                
            analysis_result = self._process_data_with_agent(prompt, {
                "ticker": ticker,
                "historical_data": historical_data,
                "technical_indicators": technical_indicators
            })
            
            # 返回结果
            return {
                "stock_data": stock_data,
                "analysis": analysis_result,
                "messages": []  # 暂时返回空消息列表
            }
            
        except Exception as e:
            self.logger.error(f"获取市场数据时发生错误: {str(e)}")
            raise e
    
    def _get_historical_data(self, ticker: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取历史价格数据
        
        Args:
            ticker: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 历史价格数据
        """
        try:
            self.logger.info(f"获取历史价格数据: {ticker} 从 {start_date} 到 {end_date}")
            
            # 使用真实API获取数据
            from src.tools.api import get_price_data
            
            # 获取价格数据
            df = get_price_data(ticker, start_date, end_date)
            
            if df is None or df.empty:
                self.logger.warning(f"无法获取{ticker}的价格数据，将使用空数据继续")
                return {
                    "raw": {"dates": [], "prices": [], "volumes": []},
                    "summary": {
                        "ticker": ticker,
                        "start_date": start_date,
                        "end_date": end_date,
                        "latest_price": 0,
                        "price_change": 0,
                        "high_price": 0,
                        "low_price": 0,
                        "average_volume": 0
                    }
                }
            
            # 将DataFrame转换为可处理的字典格式
            dates = df['date'].dt.strftime('%Y-%m-%d').tolist()
            prices = df['close'].tolist()
            volumes = df['volume'].tolist()
            
            # 计算汇总数据
            latest_price = prices[-1] if prices else 0
            previous_price = prices[-2] if len(prices) > 1 else latest_price
            price_change = ((latest_price - previous_price) / previous_price * 100) if previous_price else 0
            high_price = max(prices) if prices else 0
            low_price = min(prices) if prices else 0
            
            # 构建结果
            result = {
                "raw": {
                    "dates": dates,
                    "prices": prices,
                    "volumes": volumes
                },
                "summary": {
                    "ticker": ticker,
                    "start_date": start_date,
                    "end_date": end_date,
                    "latest_price": latest_price,
                    "price_change": round(price_change, 2),
                    "high_price": high_price,
                    "low_price": low_price,
                    "average_volume": sum(volumes) / len(volumes) if volumes else 0
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取历史价格数据时发生错误: {str(e)}")
            # 返回最小数据集以避免整个流程中断
            return {
                "raw": {"dates": [], "prices": [], "volumes": []},
                "summary": {
                    "ticker": ticker,
                    "start_date": start_date,
                    "end_date": end_date,
                    "latest_price": 0,
                    "price_change": 0,
                    "high_price": 0,
                    "low_price": 0,
                    "average_volume": 0,
                    "error": str(e)
                }
            }
    
    def _calculate_technical_indicators(self, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算技术指标
        
        Args:
            historical_data: 历史价格数据
            
        Returns:
            Dict[str, Any]: 技术指标数据
        """
        try:
            from src.tools.data_helper import calculate_technical_indicators
            
            raw_data = historical_data.get("raw", {})
            dates = raw_data.get("dates", [])
            prices = raw_data.get("prices", [])
            volumes = raw_data.get("volumes", [])
            
            if not prices:
                return {}
                
            # 将数据转换为DataFrame格式，以便使用data_helper中的函数
            df = pd.DataFrame({
                "日期": dates if dates else [],
                "收盘": prices if prices else [],
                "成交量": volumes if volumes else []
            })
            
            # 记录使用的列名
            self.logger.info(f"DataFrame列名: {df.columns.tolist()}")
            
            # 使用data_helper中的函数计算技术指标
            indicators = calculate_technical_indicators(df)
            
            if indicators and "error" in indicators:
                self.logger.error(f"计算技术指标时出错: {indicators['error']}")
                return {}
            
            # 提取最新的技术指标值用于摘要
            latest_indicators = {}
            
            # 提取SMA (简单移动平均线)
            for period in [5, 10, 20, 50, 200]:
                key = f"ma_{period}"
                if key in indicators and indicators[key]:
                    latest_indicators[key] = indicators[key][-1]
                    
            # 提取RSI (相对强弱指数)
            if "rsi" in indicators and indicators["rsi"]:
                latest_indicators["rsi"] = indicators["rsi"][-1]
                
            # 提取MACD
            if all(k in indicators for k in ["macd", "macd_signal", "macd_histogram"]):
                latest_indicators["macd"] = indicators["macd"][-1] if indicators["macd"] else None
                latest_indicators["macd_signal"] = indicators["macd_signal"][-1] if indicators["macd_signal"] else None
                latest_indicators["macd_histogram"] = indicators["macd_histogram"][-1] if indicators["macd_histogram"] else None
                
            # 提取布林带
            if all(k in indicators for k in ["bollinger_ma", "bollinger_upper", "bollinger_lower"]):
                latest_indicators["bollinger_middle"] = indicators["bollinger_ma"][-1] if indicators["bollinger_ma"] else None
                latest_indicators["bollinger_upper"] = indicators["bollinger_upper"][-1] if indicators["bollinger_upper"] else None
                latest_indicators["bollinger_lower"] = indicators["bollinger_lower"][-1] if indicators["bollinger_lower"] else None
            
            # 分析价格位置
            if "ma_20" in latest_indicators and "ma_50" in latest_indicators and prices:
                latest_price = prices[-1]
                latest_indicators["price_vs_ma20"] = "above" if latest_price > latest_indicators["ma_20"] else "below"
                latest_indicators["price_vs_ma50"] = "above" if latest_price > latest_indicators["ma_50"] else "below"
            
            return {
                "full": indicators,
                "latest": latest_indicators
            }
            
        except Exception as e:
            self.logger.error(f"计算技术指标时发生错误: {str(e)}")
            return {}
    
    def _prepare_summary_prompt(self, ticker: str, stock_data: StockData) -> str:
        """准备数据摘要提示
        
        Args:
            ticker: 股票代码
            stock_data: 股票数据对象
            
        Returns:
            str: 数据摘要提示
        """
        # 提取相关数据
        historical_summary = stock_data.historical_data.get("summary", {})
        technical_indicators = stock_data.technical_indicators.get("latest", {})
        
        # 构建提示
        prompt = f"""
请对以下股票数据进行分析和预处理，确认数据质量并提供简要说明。

股票: {ticker}
最新价格: {historical_summary.get('latest_price')}
涨跌幅: {historical_summary.get('price_change')}%
时间范围: {historical_summary.get('start_date')} 至 {historical_summary.get('end_date')}

主要技术指标:
- MA(5): {technical_indicators.get('ma_5')}
- MA(20): {technical_indicators.get('ma_20')}
- RSI: {technical_indicators.get('rsi')}
- MACD: {technical_indicators.get('macd')}

请分析这些数据，确认数据是否合理、完整，并提供简要的市场数据状况描述。
如果发现任何数据问题，请指出并提供可能的解决方法。
"""
        return prompt
    
    def _process_data_with_agent(self, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """使用代理处理数据并获取结果
        
        Args:
            prompt: 提示信息
            data: 要处理的数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        # 格式化数据
        data_str = self.format_data(data)
        
        # 创建完整提示
        full_prompt = f"""{prompt}

数据:
{data_str}

请以JSON格式返回结果。
"""
        try:
            # 创建消息 - 使用新的消息格式
            msg = self.generate_human_message(content=full_prompt)
            
            # 获取代理响应
            response = self.agent.step(msg)
            
            # 记录响应
            self.log_message(response.msgs[0])
            
            # 解析响应
            return self.parse_json_response(response.msgs[0].content)
            
        except Exception as e:
            self.logger.error(f"处理数据时发生错误: {str(e)}")
            return {}

    def _get_financial_data(self, ticker: str) -> Dict[str, Any]:
        """获取股票的财务数据
        
        Args:
            ticker: 股票代码
            
        Returns:
            Dict[str, Any]: 财务数据
        """
        try:
            from src.tools.data_helper import get_fundamental_data
            
            self.logger.info(f"获取财务数据: {ticker}")
            
            # 使用data_helper中的函数获取财务数据
            financial_data = get_fundamental_data(ticker)
            
            # 如果获取失败，返回空结构
            if not financial_data or "error" in financial_data:
                self.logger.error(f"获取财务数据失败: {financial_data.get('error', '未知错误')}")
                return {
                    "income_statement": {},
                    "balance_sheet": {},
                    "financial_ratios": {},
                    "quarterly_results": [],
                    "dividend_info": {},
                }
            
            # 提取并组织数据
            financial_indicators = financial_data.get("financial_indicators", {})
            income_statement = financial_data.get("income_statement", {})
            stock_info = financial_data.get("stock_info", {})
            summary = financial_data.get("summary", {})
            
            # 获取历史财务数据，默认获取最近4个季度
            historical_data = self._get_historical_financial_data(ticker, 4)
            
            # 构建返回结构
            result = {
                "income_statement": {
                    "revenue": income_statement.get("营业收入", 0),
                    "operating_income": income_statement.get("营业利润", 0),
                    "net_income": income_statement.get("净利润", 0),
                    "total_profit": income_statement.get("利润总额", 0),
                    "eps": income_statement.get("基本每股收益", 0),
                    "income_tax": income_statement.get("减:所得税", 0),
                    "interest_income": income_statement.get("利息收入", 0),
                    "interest_expense": income_statement.get("利息支出", 0),
                    "investment_income": income_statement.get("投资收益", 0),
                    "operating_expense": income_statement.get("营业支出", 0),
                    "rd_expense": income_statement.get("研发费用", 0),
                    "business_tax": income_statement.get("营业税金及附加", 0),
                    "management_expense": income_statement.get("业务及管理费用", 0),
                    "asset_impairment_loss": income_statement.get("资产减值损失", 0),
                    "credit_impairment_loss": income_statement.get("信用减值损失", 0),
                    "non_operating_income": income_statement.get("加:营业外收入", 0),
                    "non_operating_expense": income_statement.get("减:营业外支出", 0),
                    "reporting_date": income_statement.get("报告日", ""),
                    "year_over_year_growth": financial_indicators.get("净利润同比增长率", 0),
                    "diluted_eps": income_statement.get("稀释每股收益", 0),
                },
                "balance_sheet": {
                    "total_assets": financial_indicators.get("总资产", 0),
                    "total_liabilities": financial_indicators.get("总负债", 0),
                    "total_equity": financial_indicators.get("所有者权益", 0),
                    "cash_and_equivalents": financial_indicators.get("货币资金", 0),
                    "total_debt": financial_indicators.get("带息债务", 0),
                    "retained_earnings": income_statement.get("未分配利润", 0),
                },
                "financial_ratios": {
                    "pe_ratio": stock_info.get("市盈率-动态", 0),
                    "pb_ratio": stock_info.get("市净率", 0),
                    "roe": financial_indicators.get("净资产收益率", 0),
                    "debt_to_equity": financial_indicators.get("资产负债率", 0),
                    "profit_margin": financial_indicators.get("净利率", 0),
                    "current_ratio": financial_indicators.get("流动比率", 0),
                    "turnover_rate": stock_info.get("换手率", 0),
                    "amplitude": stock_info.get("振幅", 0),
                    "year_to_date_change": stock_info.get("年初至今涨跌幅", 0),
                    "sixty_day_change": stock_info.get("60日涨跌幅", 0),
                },
                "market_info": {
                    "market_cap": stock_info.get("总市值", 0),
                    "circulating_market_value": stock_info.get("流通市值", 0),
                    "industry": summary.get("industry", ""),
                    "name": stock_info.get("名称", ""),
                    "latest_price": stock_info.get("最新价", 0),
                    "change_percent": stock_info.get("涨跌幅", 0),
                    "change_amount": stock_info.get("涨跌额", 0),
                    "volume": stock_info.get("成交量", 0),
                    "turnover": stock_info.get("成交额", 0),
                    "highest": stock_info.get("最高", 0),
                    "lowest": stock_info.get("最低", 0),
                    "open": stock_info.get("今开", 0),
                    "prev_close": stock_info.get("昨收", 0),
                },
                "historical_data": historical_data,
                "trends": self._calculate_financial_trends(historical_data)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取财务数据时发生错误: {str(e)}")
            # 返回基本数据结构以避免流程中断
            return {
                "income_statement": {},
                "balance_sheet": {},
                "financial_ratios": {},
                "market_info": {},
                "historical_data": [],
                "trends": {},
                "error": str(e)
            }
    
    def _get_historical_financial_data(self, ticker: str, num_quarters: int = 4) -> List[Dict[str, Any]]:
        """获取历史财务数据
        
        Args:
            ticker: 股票代码
            num_quarters: 要获取的季度数量
            
        Returns:
            List[Dict[str, Any]]: 历史财务数据列表
        """
        try:
            import akshare as ak
            
            self.logger.info(f"获取{ticker}的历史财务数据，共{num_quarters}个季度")
            
            # 确定股票前缀
            stock_prefix = 'sz' if ticker.startswith('0') or ticker.startswith('3') else 'sh'
            formatted_ticker = f"{stock_prefix}{ticker}"
            
            # 获取利润表数据
            income_statements = ak.stock_financial_report_sina(stock=formatted_ticker, symbol="利润表")
            
            # 获取资产负债表数据
            try:
                balance_sheets = ak.stock_financial_report_sina(stock=formatted_ticker, symbol="资产负债表")
            except Exception as e:
                self.logger.warning(f"获取{ticker}的资产负债表数据失败: {str(e)}")
                balance_sheets = pd.DataFrame()
            
            # 获取现金流量表数据
            try:
                cash_flows = ak.stock_financial_report_sina(stock=formatted_ticker, symbol="现金流量表")
            except Exception as e:
                self.logger.warning(f"获取{ticker}的现金流量表数据失败: {str(e)}")
                cash_flows = pd.DataFrame()
            
            # 获取财务指标数据
            try:
                financial_indicators = ak.stock_financial_analysis_indicator(symbol=ticker)
            except Exception as e:
                self.logger.warning(f"获取{ticker}的财务指标数据失败: {str(e)}")
                financial_indicators = pd.DataFrame()
            
            # 限制数量
            if not income_statements.empty:
                income_statements = income_statements.head(num_quarters)
            if not balance_sheets.empty:
                balance_sheets = balance_sheets.head(num_quarters)
            if not cash_flows.empty:
                cash_flows = cash_flows.head(num_quarters)
            if not financial_indicators.empty:
                financial_indicators = financial_indicators.head(num_quarters)
            
            # 组织历史数据
            historical_data = []
            
            # 使用利润表的报告日期作为基准
            if not income_statements.empty:
                for i, row in income_statements.iterrows():
                    if i >= num_quarters:
                        break
                    
                    report_date = row.get("报告日", "")
                    
                    # 查找相应日期的资产负债表和现金流量表数据
                    balance_sheet_row = balance_sheets[balance_sheets["报告日"] == report_date].iloc[0] if not balance_sheets.empty and report_date in balance_sheets["报告日"].values else pd.Series()
                    cash_flow_row = cash_flows[cash_flows["报告日"] == report_date].iloc[0] if not cash_flows.empty and report_date in cash_flows["报告日"].values else pd.Series()
                    
                    # 提取财务指标数据
                    financial_indicator_row = pd.Series()
                    if not financial_indicators.empty:
                        # 处理财务指标数据，通常日期格式不同，需要转换
                        for _, indicator_row in financial_indicators.iterrows():
                            indicator_date = indicator_row.get("日期")
                            if indicator_date and str(indicator_date).replace("-", "").startswith(report_date[:6]):
                                financial_indicator_row = indicator_row
                                break
                    
                    # 组织单季度数据
                    quarter_data = {
                        "report_date": report_date,
                        "formatted_date": f"{report_date[:4]}年{report_date[4:6]}月{report_date[6:]}日",
                        "income_statement": {
                            "revenue": row.get("营业收入", 0),
                            "operating_profit": row.get("营业利润", 0),
                            "net_income": row.get("净利润", 0),
                            "total_profit": row.get("利润总额", 0),
                            "eps": row.get("基本每股收益", 0),
                        },
                        "balance_sheet": {
                            "total_assets": balance_sheet_row.get("资产总计", 0),
                            "total_liabilities": balance_sheet_row.get("负债合计", 0),
                            "equity": balance_sheet_row.get("所有者权益(或股东权益)合计", 0),
                            "cash": balance_sheet_row.get("货币资金", 0),
                        },
                        "cash_flow": {
                            "operating_cash_flow": cash_flow_row.get("经营活动产生的现金流量净额", 0),
                            "investing_cash_flow": cash_flow_row.get("投资活动产生的现金流量净额", 0),
                            "financing_cash_flow": cash_flow_row.get("筹资活动产生的现金流量净额", 0),
                        },
                        "financial_indicators": {
                            "roe": financial_indicator_row.get("净资产收益率(%)", 0),
                            "gross_margin": financial_indicator_row.get("销售毛利率(%)", 0),
                            "debt_ratio": financial_indicator_row.get("资产负债率(%)", 0),
                        }
                    }
                    
                    historical_data.append(quarter_data)
            
            self.logger.info(f"成功获取{ticker}的历史财务数据，共{len(historical_data)}个季度")
            return historical_data
            
        except Exception as e:
            self.logger.error(f"获取历史财务数据时发生错误: {str(e)}")
            return []
    
    def _calculate_financial_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算财务趋势
        
        Args:
            historical_data: 历史财务数据列表
            
        Returns:
            Dict[str, Any]: 财务趋势数据
        """
        if not historical_data or len(historical_data) < 2:
            return {}
        
        # 提取关键指标的时间序列
        revenue_trend = []
        net_income_trend = []
        eps_trend = []
        roe_trend = []
        
        for quarter in historical_data:
            revenue_trend.append(float(quarter["income_statement"]["revenue"]))
            net_income_trend.append(float(quarter["income_statement"]["net_income"]))
            eps_trend.append(float(quarter["income_statement"]["eps"]))
            roe_trend.append(float(quarter["financial_indicators"]["roe"]))
        
        # 计算同比增长率
        try:
            revenue_growth = (revenue_trend[0] - revenue_trend[-1]) / revenue_trend[-1] * 100 if revenue_trend[-1] else 0
            net_income_growth = (net_income_trend[0] - net_income_trend[-1]) / net_income_trend[-1] * 100 if net_income_trend[-1] else 0
        except (IndexError, ZeroDivisionError):
            revenue_growth = 0
            net_income_growth = 0
        
        # 计算趋势
        trends = {
            "revenue": {
                "values": revenue_trend,
                "growth": revenue_growth,
                "trend": "上升" if revenue_growth > 0 else "下降" if revenue_growth < 0 else "持平"
            },
            "net_income": {
                "values": net_income_trend,
                "growth": net_income_growth,
                "trend": "上升" if net_income_growth > 0 else "下降" if net_income_growth < 0 else "持平"
            },
            "eps": {
                "values": eps_trend,
                "trend": "上升" if eps_trend[0] > eps_trend[-1] else "下降" if eps_trend[0] < eps_trend[-1] else "持平"
            },
            "roe": {
                "values": roe_trend,
                "trend": "上升" if roe_trend[0] > roe_trend[-1] else "下降" if roe_trend[0] < roe_trend[-1] else "持平"
            }
        }
        
        return trends
    
    def _get_news_data(self, ticker: str, num_of_news: int = 5) -> Dict[str, Any]:
        """获取股票相关的新闻数据
        
        Args:
            ticker: 股票代码
            num_of_news: 获取的新闻数量
            
        Returns:
            Dict[str, Any]: 新闻数据
        """
        try:
            from src.tools.data_helper import get_stock_news
            
            self.logger.info(f"获取新闻数据: {ticker}, 数量: {num_of_news}")
            
            # 使用data_helper中的函数获取新闻数据
            news_list = get_stock_news(ticker, num_of_news)
            
            # 如果没有获取到新闻，返回空结构
            if not news_list:
                return {
                    "news": [],
                    "overall_sentiment": 0,
                    "sentiment_breakdown": {"positive": 0, "neutral": 0, "negative": 0}
                }
            
            # 简单情感分析 (实际应用中应使用NLP模型进行分析)
            # 这里使用模型分析标题进行简单情感判断
            sentiment_scores = []
            sentiments = {"positive": 0, "neutral": 0, "negative": 0}
            
            for news in news_list:
                # 让LLM对新闻标题进行情感分析
                sentiment_prompt = f"""
                请分析以下新闻标题的情感倾向，仅回复"positive"、"neutral"或"negative"：
                {news.get('title', '')}
                """
                
                try:
                    # 使用LLM分析情感
                    msg = self.generate_human_message(content=sentiment_prompt)
                    response = self.agent.step(msg)
                    sentiment = response.msgs[0].content.strip().lower()
                    
                    # 规范化情感结果
                    if "positive" in sentiment:
                        news["sentiment"] = "positive"
                        news["sentiment_score"] = 0.8
                        sentiments["positive"] += 1
                        sentiment_scores.append(0.8)
                    elif "negative" in sentiment:
                        news["sentiment"] = "negative"
                        news["sentiment_score"] = -0.7
                        sentiments["negative"] += 1
                        sentiment_scores.append(-0.7)
                    else:
                        news["sentiment"] = "neutral"
                        news["sentiment_score"] = 0.1
                        sentiments["neutral"] += 1
                        sentiment_scores.append(0.1)
                        
                except Exception:
                    # 如果LLM分析失败，默认为中性
                    news["sentiment"] = "neutral"
                    news["sentiment_score"] = 0.0
                    sentiments["neutral"] += 1
                    sentiment_scores.append(0.0)
            
            # 计算总体情感得分
            overall_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            return {
                "news": news_list,
                "overall_sentiment": overall_sentiment,
                "sentiment_breakdown": sentiments
            }
            
        except Exception as e:
            self.logger.error(f"获取新闻数据时发生错误: {str(e)}")
            # 返回基本数据结构以避免流程中断
            return {
                "news": [],
                "overall_sentiment": 0,
                "sentiment_breakdown": {"positive": 0, "neutral": 0, "negative": 0},
                "error": str(e)
            } 