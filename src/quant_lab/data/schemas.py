"""数据模型定义"""

from datetime import date

from pydantic import BaseModel


class DailyBar(BaseModel):
    """日线数据"""

    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float = 0.0  # 成交额

    # 可选字段
    turnover: float = 0.0  # 换手率
    pre_close: float = 0.0  # 前收盘价


class StockInfo(BaseModel):
    """股票基本信息"""

    symbol: str  # 股票代码如 600000
    name: str  # 股票名称
    market: str  # 市场：SH/SZ
    board: str = "main"  # 板块：main/gem/star（主板/创业板/科创板）


class FetchRequest(BaseModel):
    """数据采集请求"""

    symbol: str
    start_date: date
    end_date: date
    market: str = "auto"  # auto: 根据代码自动判断
