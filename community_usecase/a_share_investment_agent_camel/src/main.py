"""
基于Camel框架的A股投资代理系统主程序
"""
import argparse
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.agents.market_data_agent import MarketDataAgent
from src.agents.technical_analyst import TechnicalAnalystAgent
from src.agents.fundamentals_analyst import FundamentalsAnalystAgent
from src.agents.sentiment_analyst import SentimentAnalystAgent
from src.agents.valuation_analyst import ValuationAnalystAgent
from src.agents.researcher_bull import ResearcherBullAgent
from src.agents.researcher_bear import ResearcherBearAgent
from src.agents.debate_room import DebateRoomAgent
from src.agents.risk_manager import RiskManagerAgent
from src.agents.portfolio_manager import PortfolioManagerAgent
from src.models import Portfolio, TradingDecision, AnalysisSignal, StockData

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/main.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Main")


def run_investment_analysis(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    portfolio: Optional[Dict[str, Any]] = None,
    show_reasoning: bool = False,
    num_of_news: int = 5,
    model_name: str = "gemini"
) -> TradingDecision:
    """
    运行投资分析流程
    
    Args:
        ticker: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        portfolio: 当前投资组合状态
        show_reasoning: 是否显示推理过程
        num_of_news: 情绪分析使用的新闻数量
        model_name: 使用的模型名称 (gemini, openai, qwen)
        
    Returns:
        TradingDecision: 交易决策
    """
    logger.info(f"开始对 {ticker} 进行投资分析，使用模型: {model_name}")
    
    # 设置默认日期
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date_obj = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=365)
        start_date = start_date_obj.strftime("%Y-%m-%d")
    
    # 设置默认投资组合
    if not portfolio:
        portfolio = {"cash": 100000.0, "stock": 0}
    
    # 初始数据
    data = {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "portfolio": portfolio,
        "num_of_news": num_of_news
    }
    
    # 创建代理
    market_data_agent = MarketDataAgent(show_reasoning=show_reasoning, model_name=model_name)
    technical_analyst = TechnicalAnalystAgent(show_reasoning=show_reasoning, model_name=model_name)
    fundamentals_analyst = FundamentalsAnalystAgent(show_reasoning=show_reasoning, model_name=model_name)
    sentiment_analyst = SentimentAnalystAgent(show_reasoning=show_reasoning, model_name=model_name)
    valuation_analyst = ValuationAnalystAgent(show_reasoning=show_reasoning, model_name=model_name)
    researcher_bull = ResearcherBullAgent(show_reasoning=show_reasoning, model_name=model_name)
    researcher_bear = ResearcherBearAgent(show_reasoning=show_reasoning, model_name=model_name)
    debate_room = DebateRoomAgent(show_reasoning=show_reasoning, model_name=model_name)
    risk_manager = RiskManagerAgent(show_reasoning=show_reasoning, model_name=model_name)
    portfolio_manager = PortfolioManagerAgent(show_reasoning=show_reasoning, model_name=model_name)
    
    try:
        # 第一步: 获取市场数据
        logger.info("步骤1: 获取市场数据")
        market_data_result = market_data_agent.process(data)
        
        # 提取股票数据
        stock_data = market_data_result.get("stock_data")
        if not stock_data:
            raise ValueError("市场数据代理未返回股票数据")
        
        # 第二步: 技术分析
        logger.info("步骤2: 进行技术分析")
        technical_data = {
            "stock_data": stock_data,
            "messages": market_data_result.get("messages", [])
        }
        technical_result = technical_analyst.process(technical_data)
        technical_analysis = technical_result.get("technical_analysis")
        
        # 第三步: 基本面分析
        logger.info("步骤3: 进行基本面分析")
        fundamentals_data = {
            "stock_data": stock_data,
            "messages": technical_result.get("messages", [])
        }
        fundamentals_result = fundamentals_analyst.process(fundamentals_data)
        fundamentals_analysis = fundamentals_result.get("fundamentals_analysis")
        
        # 第四步: 情绪分析
        logger.info("步骤4: 进行情绪分析")
        sentiment_data = {
            "stock_data": stock_data,
            "messages": fundamentals_result.get("messages", [])
        }
        sentiment_result = sentiment_analyst.process(sentiment_data)
        sentiment_analysis = sentiment_result.get("sentiment_analysis")
        
        # 第五步: 估值分析
        logger.info("步骤5: 进行估值分析")
        valuation_data = {
            "stock_data": stock_data,
            "fundamentals_analysis": fundamentals_analysis,
            "messages": sentiment_result.get("messages", [])
        }
        valuation_result = valuation_analyst.process(valuation_data)
        valuation_analysis = valuation_result.get("valuation_analysis")
        
        # 第六步: 多头研究员报告
        logger.info("步骤6: 生成多头研究报告")
        bull_data = {
            "stock_data": stock_data,
            "technical_analysis": technical_analysis,
            "fundamentals_analysis": fundamentals_analysis,
            "sentiment_analysis": sentiment_analysis,
            "valuation_analysis": valuation_analysis,
            "messages": valuation_result.get("messages", [])
        }
        bull_result = researcher_bull.process(bull_data)
        bull_research = bull_result.get("bull_research")
        
        # 第七步: 空头研究员报告
        logger.info("步骤7: 生成空头研究报告")
        bear_data = {
            "stock_data": stock_data,
            "technical_analysis": technical_analysis,
            "fundamentals_analysis": fundamentals_analysis,
            "sentiment_analysis": sentiment_analysis,
            "valuation_analysis": valuation_analysis,
            "messages": bull_result.get("messages", [])
        }
        bear_result = researcher_bear.process(bear_data)
        bear_research = bear_result.get("bear_research")
        
        # 第八步: 辩论室
        logger.info("步骤8: 举行辩论会")
        debate_data = {
            "stock_data": stock_data,
            "bull_research": bull_research,
            "bear_research": bear_research,
            "messages": bear_result.get("messages", [])
        }
        debate_result = debate_room.process(debate_data)
        debate_signal = debate_result.get("debate_result")
        
        # 第九步: 风险评估
        logger.info("步骤9: 进行风险评估")
        risk_data = {
            "stock_data": stock_data,
            "debate_result": debate_signal,
            "portfolio": portfolio,
            "messages": debate_result.get("messages", [])
        }
        risk_result = risk_manager.process(risk_data)
        risk_analysis = risk_result.get("risk_analysis")
        
        # 第十步: 投资组合管理
        logger.info("步骤10: 制定最终投资决策")
        portfolio_data = {
            "stock_data": stock_data,
            "technical_analysis": technical_analysis,
            "fundamentals_analysis": fundamentals_analysis,
            "sentiment_analysis": sentiment_analysis,
            "valuation_analysis": valuation_analysis,
            "debate_result": debate_signal,
            "risk_analysis": risk_analysis,
            "portfolio": portfolio,
            "messages": risk_result.get("messages", [])
        }
        portfolio_result = portfolio_manager.process(portfolio_data)
        trading_decision = portfolio_result.get("trading_decision")
        
        logger.info(f"投资分析完成，决策: {trading_decision.action}, 数量: {trading_decision.quantity}")
        return trading_decision
        
    except Exception as e:
        logger.error(f"投资分析过程中发生错误: {str(e)}")
        
        # 返回默认决策
        default_decision = TradingDecision(
            action="hold",
            quantity=0,
            confidence=0.5,
            agent_signals=[],
            reasoning=f"分析过程中发生错误: {str(e)}"
        )
        return default_decision


def test(ticker: str = "000001", model_name: str = "gemini"):
    """
    测试函数，使用预设参数快速测试系统功能
    
    Args:
        ticker: 股票代码，默认为"000001"（平安银行）
        model_name: 使用的模型名称 (gemini, openai, qwen)
    """
    logger.info(f"开始测试功能，分析股票: {ticker}")
    
    # 预设参数
    show_reasoning = True  # 显示推理过程
    num_of_news = 5  # 获取5条新闻
    initial_capital = 100000.0  # 初始资金10万元
    
    # 日期设置（默认分析最近30天）
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date_obj = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=30)
    start_date = start_date_obj.strftime("%Y-%m-%d")
    
    # 创建投资组合
    portfolio = {
        "cash": initial_capital,
        "stock": 0
    }
    
    print(f"测试配置:")
    print(f"- 股票: {ticker}")
    print(f"- 模型: {model_name}")
    print(f"- 时间范围: {start_date} 至 {end_date}")
    print(f"- 初始资金: {initial_capital}")
    print(f"- 新闻数量: {num_of_news}")
    print("\n开始分析...\n")
    
    # 运行投资分析
    decision = run_investment_analysis(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        show_reasoning=show_reasoning,
        num_of_news=num_of_news,
        model_name=model_name
    )
    
    # 输出结果
    print("\n测试结果 - 交易决策:")
    print(json.dumps(decision.dict(), indent=2, ensure_ascii=False))
    return decision


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="基于Camel框架的A股投资代理系统")
    parser.add_argument("--ticker", type=str, required=True, help="股票代码")
    parser.add_argument("--start-date", type=str, help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--cash", type=float, default=100000.0, help="初始现金")
    parser.add_argument("--stock", type=int, default=0, help="初始股票数量")
    parser.add_argument("--model", type=str, default="qwen", choices=["gemini", "openai", "qwen"], help="使用的模型")
    parser.add_argument("--news", type=int, default=10, help="情绪分析的新闻数量")
    parser.add_argument("--show-reasoning", action="store_true", help="显示详细推理过程")
    parser.add_argument("--test", action="store_true", help="以测试模式运行，使用默认参数")
    
    args = parser.parse_args()
    
    # 测试模式
    if args.test:
        test(ticker=args.ticker, model_name=args.model)
        return
    
    # 正常模式，使用命令行参数
    portfolio = {
        "cash": args.cash,
        "stock": args.stock
    }
    
    decision = run_investment_analysis(
        ticker=args.ticker,
        start_date=args.start_date,
        end_date=args.end_date,
        portfolio=portfolio,
        show_reasoning=args.show_reasoning,
        num_of_news=args.news,
        model_name=args.model
    )
    
    print(json.dumps(decision.dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main() 