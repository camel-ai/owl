"""
数据API接口模块
"""
import pandas as pd
import akshare as ak
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_price_data(ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    获取股票价格数据
    
    Args:
        ticker: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Returns:
        Optional[pd.DataFrame]: 股票价格数据
    """
    try:
        logger.info(f"获取股票 {ticker} 的价格数据")
        
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
        
        # 检查df的列数
        logger.info(f"原始数据列: {df.columns.tolist()}")
        
        # 调整列名映射以适应实际返回的数据
        column_mappings = {
            '日期': 'date',
            '股票代码': 'code',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turnover'
        }
        
        # 根据实际列名重命名
        new_columns = []
        for col in df.columns:
            if col in column_mappings:
                new_columns.append(column_mappings[col])
            else:
                # 保留原列名
                new_columns.append(col)
        
        # 应用新列名
        df.columns = new_columns
        
        # 将日期列转换为datetime类型
        df['date'] = pd.to_datetime(df['date'])
        
        logger.info(f"成功获取价格数据，共 {len(df)} 条记录")
        return df
        
    except Exception as e:
        logger.error(f"获取价格数据时发生错误: {str(e)}")
        return None 