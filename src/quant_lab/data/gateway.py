"""数据网关抽象基类（参考 vnpy Gateway 模式）"""

from abc import ABC, abstractmethod

import polars as pl

from .schemas import FetchRequest


class BaseGateway(ABC):
    """数据网关抽象基类

    所有数据源（AKShare、Tushare 等）都实现此接口。
    换数据源只需新增一个 Gateway 实现，不影响上层逻辑。
    """

    @abstractmethod
    def fetch_daily(self, request: FetchRequest) -> pl.DataFrame:
        """获取日线数据

        Args:
            request: 数据采集请求

        Returns:
            包含 date, open, high, low, close, volume 列的 DataFrame
        """
        ...

    @abstractmethod
    def get_stock_list(self) -> pl.DataFrame:
        """获取股票列表

        Returns:
            包含 symbol, name, market 列的 DataFrame
        """
        ...
