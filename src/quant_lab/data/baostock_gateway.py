"""Baostock（证券宝）数据网关实现

Baostock 是免费的 A 股数据源，无需注册，直连服务器。
"""

import baostock as bs
import polars as pl
from loguru import logger

from .gateway import BaseGateway
from .schemas import FetchRequest


def _symbol_to_bscode(symbol: str, market: str = "auto") -> str:
    """将股票代码转换为 Baostock 格式

    Baostock 格式：sh.600000 / sz.000001
    """
    code = symbol.replace("SH", "").replace("SZ", "").replace(".", "")
    if market == "auto":
        market = "sh" if code.startswith("6") else "sz"
    else:
        market = market.lower()
    return f"{market}.{code}"


class BaostockGateway(BaseGateway):
    """Baostock 数据网关

    通过 Baostock 库获取 A 股数据。
    免费、无需注册、直连服务器、无反爬限制。
    """

    def __init__(self):
        self._logged_in = False

    def _ensure_login(self):
        if not self._logged_in:
            lg = bs.login()
            if lg.error_code != "0":
                raise RuntimeError(f"Baostock login failed: {lg.error_msg}")
            self._logged_in = True

    def _logout(self):
        if self._logged_in:
            bs.logout()
            self._logged_in = False

    def fetch_daily(self, request: FetchRequest) -> pl.DataFrame:
        """获取日线数据"""
        self._ensure_login()
        bs_code = _symbol_to_bscode(request.symbol, request.market)
        start = request.start_date.strftime("%Y-%m-%d")
        end = request.end_date.strftime("%Y-%m-%d")

        logger.info(f"Fetching daily data: {bs_code} from {start} to {end}")

        fields = "date,open,high,low,close,volume,amount,turn,pctChg"
        rs = bs.query_history_k_data_plus(
            bs_code,
            fields,
            start_date=start,
            end_date=end,
            frequency="d",
            adjustflag="2",  # 前复权
        )

        if rs.error_code != "0":
            raise RuntimeError(f"Baostock query failed: {rs.error_msg}")

        data = []
        while rs.error_code == "0" and rs.next():
            data.append(rs.get_row_data())

        if not data:
            logger.warning(f"No data returned for {bs_code}")
            return pl.DataFrame()

        df = pl.DataFrame(data, schema=fields.split(","), orient="row")

        # 类型转换
        df = df.with_columns(
            pl.col("date").str.to_date("%Y-%m-%d"),
            pl.col("open").cast(pl.Float64),
            pl.col("high").cast(pl.Float64),
            pl.col("low").cast(pl.Float64),
            pl.col("close").cast(pl.Float64),
            pl.col("volume").cast(pl.Float64),
        )

        # 可选列
        for col in ["amount", "turn", "pctChg"]:
            if col in df.columns:
                df = df.with_columns(pl.col(col).cast(pl.Float64))

        # 添加前收盘价
        df = df.with_columns(
            pl.col("close").shift(1).alias("pre_close")
        )

        # 过滤空行（停牌日）
        df = df.filter(pl.col("close") > 0)

        logger.info(f"Fetched {len(df)} rows for {bs_code}")
        return df

    def get_stock_list(self) -> pl.DataFrame:
        """获取 A 股股票列表"""
        self._ensure_login()

        logger.info("Fetching A-share stock list")

        # 获取最新交易日的股票列表
        rs = bs.query_stock_basic()
        if rs.error_code != "0":
            raise RuntimeError(f"Baostock query_stock_basic failed: {rs.error_msg}")

        data = []
        while rs.error_code == "0" and rs.next():
            data.append(rs.get_row_data())

        if not data:
            return pl.DataFrame()

        # fields: code, code_name, ipoDate, outDate, type, status
        df = pl.DataFrame(
            data,
            schema=["code", "code_name", "ipoDate", "outDate", "type", "status"],
            orient="row",
        )

        # 只保留股票（type=1）且状态正常（status=1）
        df = df.filter(
            (pl.col("type") == "1") & (pl.col("status") == "1")
        )

        # 提取纯代码和市场
        df = df.with_columns(
            pl.col("code").str.split(".").list.get(1).alias("symbol"),
            pl.col("code").str.split(".").list.get(0).str.to_uppercase().alias("market"),
            pl.col("code_name").alias("name"),
        )

        return df.select(["symbol", "name", "market"])
