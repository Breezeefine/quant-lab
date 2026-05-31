"""AKShare 数据网关实现"""

import time

import akshare as ak
import polars as pl
from loguru import logger

from .gateway import BaseGateway
from .schemas import FetchRequest


def _symbol_to_akcode(symbol: str, market: str = "auto") -> str:
    """将股票代码转换为 AKShare 格式

    AKShare 的 stock_zh_a_hist 接口需要纯数字代码如 "600000"
    """
    # 去掉可能的市场前缀
    code = symbol.replace("SH", "").replace("SZ", "").replace(".", "")
    return code


class AKShareGateway(BaseGateway):
    """AKShare 数据网关

    通过 AKShare 库获取 A 股数据。
    AKShare 免费、无需注册、覆盖面广。
    """

    def __init__(self, retry_count: int = 3, retry_delay: float = 2.0):
        self.retry_count = retry_count
        self.retry_delay = retry_delay

    def fetch_daily(self, request: FetchRequest) -> pl.DataFrame:
        """获取日线数据

        使用 akshare 的 stock_zh_a_hist 接口。
        """
        code = _symbol_to_akcode(request.symbol, request.market)
        start = request.start_date.strftime("%Y%m%d")
        end = request.end_date.strftime("%Y%m%d")

        logger.info(f"Fetching daily data: {code} from {start} to {end}")

        for attempt in range(self.retry_count):
            try:
                df_pd = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start,
                    end_date=end,
                    adjust="qfq",  # 前复权
                )
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError(f"Failed to fetch data after {self.retry_count} attempts: {e}")

        # 转换为 Polars DataFrame
        df = pl.from_pandas(df_pd)

        # 统一列名（AKShare 中文列名 → 英文列名）
        column_mapping = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "pct_change",
            "涨跌额": "change",
            "换手率": "turnover",
        }

        # 只重命名存在的列
        rename_map = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(rename_map)

        # 确保 date 列是 date 类型
        if "date" in df.columns:
            df = df.with_columns(pl.col("date").cast(pl.Date))

        # 选择需要的列
        keep_cols = ["date", "open", "high", "low", "close", "volume", "amount"]
        available = [c for c in keep_cols if c in df.columns]
        df = df.select(available)

        # 添加前收盘价（用于涨跌停计算）
        if "close" in df.columns:
            df = df.with_columns(
                pl.col("close").shift(1).alias("pre_close")
            )

        logger.info(f"Fetched {len(df)} rows for {code}")
        return df

    def get_stock_list(self) -> pl.DataFrame:
        """获取 A 股股票列表"""
        logger.info("Fetching A-share stock list")

        for attempt in range(self.retry_count):
            try:
                df_pd = ak.stock_zh_a_spot_em()
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError(f"Failed to fetch stock list: {e}")

        df = pl.from_pandas(df_pd)

        # 统一列名
        column_mapping = {
            "代码": "symbol",
            "名称": "name",
        }
        rename_map = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(rename_map)

        # 判断市场
        if "symbol" in df.columns:
            df = df.with_columns(
                pl.when(pl.col("symbol").str.starts_with("6"))
                .then(pl.lit("SH"))
                .otherwise(pl.lit("SZ"))
                .alias("market")
            )

        keep_cols = ["symbol", "name", "market"]
        available = [c for c in keep_cols if c in df.columns]
        return df.select(available)
