"""
数据辅助工具模块
"""
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def get_stock_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取股票历史数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Returns:
        pd.DataFrame: 股票历史数据
    """
    try:
        logger.info(f"获取股票 {ticker} 的历史数据")
        
        # 转换日期格式
        start_date_fmt = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y%m%d")
        end_date_fmt = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y%m%d")
        
        # 使用akshare获取A股历史数据
        df = ak.stock_zh_a_hist(
            symbol=ticker,
            period="daily",
            start_date=start_date_fmt,
            end_date=end_date_fmt,
            adjust="qfq"  # 前复权
        )
        
        logger.info(f"成功获取历史数据，共 {len(df)} 条记录")
        return df
        
    except Exception as e:
        logger.error(f"获取历史数据时发生错误: {str(e)}")
        return pd.DataFrame()


def get_fundamental_data(ticker: str) -> Dict[str, Any]:
    """
    获取股票基本面数据
    
    Args:
        ticker: 股票代码
        
    Returns:
        Dict[str, Any]: 基本面数据
    """
    try:
        logger.info(f"获取股票 {ticker} 的基本面数据")
        
        # 获取财务指标数据
        financial_indicators = ak.stock_financial_analysis_indicator(symbol=ticker)
        
        # 获取利润表数据
        try:
            # 根据akshare文档修正
            # stock参数格式应该为'sh'或'sz'+股票代码，而不是直接使用数字代码
            stock_prefix = 'sz' if ticker.startswith('0') or ticker.startswith('3') else 'sh'
            formatted_ticker = f"{stock_prefix}{ticker}"
            # 必须传入symbol参数，设置为"利润表"
            income_statement = ak.stock_financial_report_sina(stock=formatted_ticker, symbol="利润表")
            logger.info(f"成功获取{ticker}的利润表数据")
        except Exception as e:
            logger.error(f"获取利润表数据时出错: {str(e)}")
            income_statement = pd.DataFrame()
        
        # 获取实时行情
        real_time_quote = ak.stock_zh_a_spot_em()
        stock_quote = real_time_quote[real_time_quote['代码'] == ticker]
        
        # 记录实时行情字段名，帮助调试
        if not stock_quote.empty:
            logger.info(f"实时行情数据字段: {stock_quote.columns.tolist()}")
        
        # 提取关键财务指标
        latest_indicators = {}
        if not financial_indicators.empty:
            latest_indicators = financial_indicators.iloc[-1].to_dict()
        
        # 提取关键利润表指标
        income_data = {}
        if not income_statement.empty:
            income_data = income_statement.iloc[-1].to_dict()
        
        # 股票基本信息
        stock_info = {}
        if not stock_quote.empty:
            stock_info = stock_quote.iloc[0].to_dict()
        
        logger.info(f"成功获取基本面数据")
        
        # 调整处理市场信息，确保字段名正确匹配
        market_summary = {
            "name": stock_info.get("名称", ""),
            "pe_ratio": stock_info.get("市盈率-动态", None),  # 调整为实际字段名
            "pb_ratio": stock_info.get("市净率", None),
            "market_cap": stock_info.get("总市值", None),
            "industry": ""  # 行情数据中没有行业信息
        }
        
        return {
            "financial_indicators": latest_indicators,
            "income_statement": income_data,
            "stock_info": stock_info,
            "summary": market_summary
        }
        
    except Exception as e:
        logger.error(f"获取基本面数据时发生错误: {str(e)}")
        return {
            "financial_indicators": {},
            "income_statement": {},
            "stock_info": {},
            "summary": {
                "name": "",
                "pe_ratio": None,
                "pb_ratio": None,
                "market_cap": None,
                "industry": ""
            },
            "error": str(e)
        }


def get_stock_news(ticker: str, num_of_news: int = 5) -> List[Dict[str, Any]]:
    """
    获取股票相关新闻
    
    Args:
        ticker: 股票代码
        num_of_news: 获取的新闻数量
        
    Returns:
        List[Dict[str, Any]]: 新闻列表
    """
    try:
        logger.info(f"获取股票 {ticker} 的新闻数据 (共{num_of_news}条)")
        
        # 获取股票名称
        real_time_quote = ak.stock_zh_a_spot_em()
        stock_quote = real_time_quote[real_time_quote['代码'] == ticker]
        stock_name = stock_quote.iloc[0]['名称'] if not stock_quote.empty else ""
        
        if not stock_name:
            logger.warning(f"无法获取股票 {ticker} 的名称")
            return []
        
        # 获取财经新闻
        news_df = ak.stock_news_em(symbol=stock_name)
        
        # 记录新闻数据字段名，帮助调试
        if not news_df.empty:
            logger.info(f"新闻数据字段: {news_df.columns.tolist()}")
        
        # 筛选最近的新闻
        recent_news = news_df.head(min(num_of_news, len(news_df)))
        
        news_list = []
        for _, row in recent_news.iterrows():
            news_list.append({
                "title": row.get("新闻标题", ""),
                "content": row.get("新闻内容", ""),
                "date": row.get("发布时间", ""),
                "source": row.get("文章来源", "")  # 调整为正确的字段名
            })
        
        logger.info(f"成功获取 {len(news_list)} 条新闻")
        return news_list
        
    except Exception as e:
        logger.error(f"获取新闻数据时发生错误: {str(e)}")
        return []


def calculate_technical_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    计算技术指标
    
    Args:
        df: 股票历史数据DataFrame
        
    Returns:
        Dict[str, Any]: 技术指标
    """
    try:
        logger.info("计算技术指标")
        
        if df.empty:
            logger.warning("没有历史数据用于计算技术指标")
            return {}
        
        # 记录实际的列名，帮助调试
        logger.info(f"传入DataFrame的列名: {df.columns.tolist()}")
        
        # 确保列名符合预期
        price_column = None
        volume_column = None
        
        # 逐个检查可能的列名
        for col_name in ["收盘", "close"]:
            if col_name in df.columns:
                price_column = col_name
                break
                
        for col_name in ["成交量", "volume"]:
            if col_name in df.columns:
                volume_column = col_name
                break
        
        if not price_column:
            logger.error("找不到有效的价格列，当前列名: " + str(df.columns.tolist()))
            return {"error": "找不到有效的价格列"}
            
        if not volume_column:
            logger.warning("找不到有效的成交量列，将只计算价格相关指标")
        
        # 提取收盘价和成交量数据
        close_prices = df[price_column].values
        volumes = df[volume_column].values if volume_column else None
        
        # 计算常用技术指标
        indicators = {}
        
        # 1. 移动平均线
        ma_windows = [5, 10, 20, 50, 200]
        for window in ma_windows:
            if len(close_prices) >= window:
                ma = pd.Series(close_prices).rolling(window=window).mean().values
                indicators[f"ma_{window}"] = ma.tolist()
        
        # 2. 相对强弱指数 (RSI)
        if len(close_prices) >= 14:
            delta = pd.Series(close_prices).diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            indicators["rsi"] = rsi.values.tolist()
        
        # 3. MACD (移动平均收敛/发散)
        if len(close_prices) >= 26:
            exp12 = pd.Series(close_prices).ewm(span=12, adjust=False).mean()
            exp26 = pd.Series(close_prices).ewm(span=26, adjust=False).mean()
            macd = exp12 - exp26
            signal = macd.ewm(span=9, adjust=False).mean()
            indicators["macd"] = macd.values.tolist()
            indicators["macd_signal"] = signal.values.tolist()
            indicators["macd_histogram"] = (macd - signal).values.tolist()
        
        # 4. 布林带
        if len(close_prices) >= 20:
            ma20 = pd.Series(close_prices).rolling(window=20).mean()
            std20 = pd.Series(close_prices).rolling(window=20).std()
            upper_band = ma20 + (std20 * 2)
            lower_band = ma20 - (std20 * 2)
            indicators["bollinger_ma"] = ma20.values.tolist()
            indicators["bollinger_upper"] = upper_band.values.tolist()
            indicators["bollinger_lower"] = lower_band.values.tolist()
        
        logger.info("成功计算技术指标")
        return indicators
        
    except Exception as e:
        logger.error(f"计算技术指标时发生错误: {str(e)}")
        return {"error": str(e)} 