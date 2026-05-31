"""数据存储层（Parquet 格式）"""

from pathlib import Path

import polars as pl
from loguru import logger

from ..config import settings


class Storage:
    """Parquet 数据存储

    目录结构：
    data/raw/cn_stock/daily/{market}{symbol}/{year}.parquet
    例如：data/raw/cn_stock/daily/SH600000/2024.parquet
    """

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or settings.raw_dir

    def _daily_path(self, symbol: str, market: str = "SH") -> Path:
        """获取日线数据目录"""
        return self.base_dir / "cn_stock" / "daily" / f"{market}{symbol}"

    def save_daily(self, df: pl.DataFrame, symbol: str, market: str = "SH") -> Path:
        """保存日线数据（按年分文件）

        Args:
            df: 日线数据 DataFrame
            symbol: 股票代码
            market: 市场（SH/SZ）

        Returns:
            保存的目录路径
        """
        path = self._daily_path(symbol, market)
        path.mkdir(parents=True, exist_ok=True)

        if "date" in df.columns:
            # 按年分文件
            df = df.with_columns(pl.col("date").dt.year().alias("year"))
            for year_val, year_df in df.group_by("year"):
                # group_by 返回元组，提取第一个元素
                year_key = year_val[0] if isinstance(year_val, tuple) else year_val
                year_file = path / f"{year_key}.parquet"
                year_df = year_df.drop("year")
                year_df.write_parquet(year_file)
                logger.info(f"Saved {len(year_df)} rows to {year_file}")
        else:
            # 没有 date 列，直接保存
            file = path / "data.parquet"
            df.write_parquet(file)
            logger.info(f"Saved {len(df)} rows to {file}")

        return path

    def load_daily(
        self,
        symbol: str,
        market: str = "SH",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pl.DataFrame:
        """加载日线数据

        Args:
            symbol: 股票代码
            market: 市场（SH/SZ）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        Returns:
            日线数据 DataFrame
        """
        path = self._daily_path(symbol, market)

        if not path.exists():
            raise FileNotFoundError(f"No data found for {market}{symbol} at {path}")

        # 读取所有 parquet 文件
        df = pl.read_parquet(path / "*.parquet")

        # 按日期排序
        if "date" in df.columns:
            df = df.sort("date")

            # 日期过滤
            if start_date:
                df = df.filter(pl.col("date") >= pl.Series([start_date]).cast(pl.Date)[0])
            if end_date:
                df = df.filter(pl.col("date") <= pl.Series([end_date]).cast(pl.Date)[0])

        logger.info(f"Loaded {len(df)} rows for {market}{symbol}")
        return df

    def list_symbols(self) -> list[str]:
        """列出已存储的股票代码"""
        daily_dir = self.base_dir / "cn_stock" / "daily"
        if not daily_dir.exists():
            return []

        symbols = []
        for path in daily_dir.iterdir():
            if path.is_dir():
                # 目录名格式：SH600000
                symbols.append(path.name)
        return sorted(symbols)

    def get_summary(self, symbol: str, market: str = "SH") -> dict:
        """获取数据摘要"""
        df = self.load_daily(symbol, market)

        if df.is_empty():
            return {"symbol": symbol, "market": market, "rows": 0}

        summary = {
            "symbol": symbol,
            "market": market,
            "rows": len(df),
            "columns": df.columns,
        }

        if "date" in df.columns:
            summary["date_range"] = (
                df["date"].min().isoformat(),
                df["date"].max().isoformat(),
            )

        if "close" in df.columns:
            summary["latest_close"] = float(df["close"].drop_nulls()[-1])

        return summary
