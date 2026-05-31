"""存储层测试"""

import tempfile
from datetime import date
from pathlib import Path

import polars as pl

from quant_lab.data.storage import Storage


class TestStorage:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = Storage(base_dir=Path(self.tmpdir))

    def _sample_df(self) -> pl.DataFrame:
        """创建测试数据"""
        return pl.DataFrame({
            "date": [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)],
            "open": [10.0, 10.2, 10.1],
            "high": [10.5, 10.6, 10.4],
            "low": [9.8, 10.0, 9.9],
            "close": [10.2, 10.3, 10.0],
            "volume": [1000000, 1200000, 900000],
        })

    def test_save_and_load(self):
        df = self._sample_df()
        self.storage.save_daily(df, "600000", "SH")

        loaded = self.storage.load_daily("600000", "SH")
        assert len(loaded) == 3
        assert "close" in loaded.columns

    def test_save_by_year(self):
        df = self._sample_df()
        path = self.storage.save_daily(df, "600000", "SH")
        # 应该有 2024.parquet
        assert (path / "2024.parquet").exists()

    def test_load_with_date_filter(self):
        df = self._sample_df()
        self.storage.save_daily(df, "600000", "SH")

        loaded = self.storage.load_daily(
            "600000", "SH",
            start_date="2024-01-03",
            end_date="2024-01-04",
        )
        assert len(loaded) == 2

    def test_load_nonexistent(self):
        try:
            self.storage.load_daily("999999", "SH")
            assert False, "Should raise FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_list_symbols(self):
        df = self._sample_df()
        self.storage.save_daily(df, "600000", "SH")
        self.storage.save_daily(df, "000001", "SZ")

        symbols = self.storage.list_symbols()
        assert "SH600000" in symbols
        assert "SZ000001" in symbols

    def test_get_summary(self):
        df = self._sample_df()
        self.storage.save_daily(df, "600000", "SH")

        summary = self.storage.get_summary("600000", "SH")
        assert summary["rows"] == 3
        assert "date_range" in summary
        assert "latest_close" in summary
