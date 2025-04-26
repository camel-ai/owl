"""
代理模块初始化
"""

from src.agents.base_agent import BaseAgent
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
from src.agents.investment_agent import InvestmentAgent

__all__ = [
    'BaseAgent',
    'MarketDataAgent', 
    'TechnicalAnalystAgent',
    'FundamentalsAnalystAgent',
    'SentimentAnalystAgent',
    'ValuationAnalystAgent',
    'ResearcherBullAgent',
    'ResearcherBearAgent',
    'DebateRoomAgent',
    'RiskManagerAgent',
    'PortfolioManagerAgent',
    'InvestmentAgent'
] 