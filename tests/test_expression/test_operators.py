"""运算符测试 — 验证每个运算符的正确性"""

import polars as pl
import pytest

from quant_lab.expression.compiler import Compiler
from quant_lab.expression.parser import Parser


@pytest.fixture
def price_df():
    """模拟价格数据"""
    return pl.DataFrame({
        "close": [10.0, 12.0, 11.0, 13.0, 15.0, 14.0, 16.0, 18.0, 17.0, 19.0],
        "open":  [9.0, 11.0, 10.0, 12.0, 14.0, 13.0, 15.0, 17.0, 16.0, 18.0],
        "high":  [11.0, 13.0, 12.0, 14.0, 16.0, 15.0, 17.0, 19.0, 18.0, 20.0],
        "low":   [9.0, 11.0, 10.0, 12.0, 14.0, 13.0, 15.0, 17.0, 16.0, 18.0],
        "volume": [100, 200, 150, 300, 250, 180, 220, 280, 190, 310],
    })


class TestOperators:
    """测试 20 个核心运算符"""

    def test_ref(self, price_df):
        result = Compiler.evaluate(price_df, "Ref($close, 1)", "f")
        assert result["f"][0] is None
        assert result["f"][1] == 10.0

    def test_ref_2(self, price_df):
        result = Compiler.evaluate(price_df, "Ref($close, 2)", "f")
        assert result["f"][0] is None
        assert result["f"][1] is None
        assert result["f"][2] == 10.0

    def test_mean(self, price_df):
        result = Compiler.evaluate(price_df, "Mean($close, 3)", "f")
        # mean(10, 12, 11) = 11.0
        assert abs(result["f"][2] - 11.0) < 1e-10

    def test_std(self, price_df):
        result = Compiler.evaluate(price_df, "Std($close, 3)", "f")
        assert result["f"][2] is not None
        assert result["f"][2] > 0

    def test_sum(self, price_df):
        result = Compiler.evaluate(price_df, "Sum($close, 3)", "f")
        # sum(10, 12, 11) = 33
        assert abs(result["f"][2] - 33.0) < 1e-10

    def test_max(self, price_df):
        result = Compiler.evaluate(price_df, "Max($close, 3)", "f")
        # max(10, 12, 11) = 12
        assert result["f"][2] == 12.0

    def test_min(self, price_df):
        result = Compiler.evaluate(price_df, "Min($close, 3)", "f")
        # min(10, 12, 11) = 10
        assert result["f"][2] == 10.0

    def test_delta(self, price_df):
        result = Compiler.evaluate(price_df, "Delta($close, 1)", "f")
        # 12 - 10 = 2
        assert abs(result["f"][1] - 2.0) < 1e-10

    def test_return(self, price_df):
        result = Compiler.evaluate(price_df, "Return($close, 1)", "f")
        # (12/10) - 1 = 0.2
        assert abs(result["f"][1] - 0.2) < 1e-10

    def test_ema(self, price_df):
        result = Compiler.evaluate(price_df, "EMA($close, 3)", "f")
        assert result["f"][0] is not None
        assert len(result["f"]) == 10

    def test_abs(self, price_df):
        df = pl.DataFrame({"close": [-1.0, 2.0, -3.0]})
        result = Compiler.evaluate(df, "Abs($close)", "f")
        assert result["f"].to_list() == [1.0, 2.0, 3.0]

    def test_log(self, price_df):
        df = pl.DataFrame({"close": [1.0, 2.718, 10.0]})
        result = Compiler.evaluate(df, "Log($close)", "f")
        assert abs(result["f"][0] - 0.0) < 0.01
        assert abs(result["f"][1] - 1.0) < 0.01

    def test_sign(self, price_df):
        df = pl.DataFrame({"close": [-5.0, 0.0, 5.0]})
        result = Compiler.evaluate(df, "Sign($close)", "f")
        assert result["f"].to_list() == [-1.0, 0.0, 1.0]

    def test_nested_mean_delta(self, price_df):
        """嵌套测试：Mean 的 Delta"""
        result = Compiler.evaluate(price_df, "Delta(Mean($close, 3), 1)", "f")
        # 第 2 行: mean(10,12,11)=11, 第 3 行: mean(12,11,13)=12, delta=1
        assert result["f"][3] is not None


class TestWithRealData:
    """用 Baostock 下载的真实数据测试"""

    @pytest.mark.slow
    def test_with_real_data(self):
        import baostock as bs
        from quant_lab.data.storage import Storage

        # 从已存储的数据加载
        storage = Storage()
        try:
            df = storage.load_daily("600000", "SH")
        except FileNotFoundError:
            pytest.skip("No data files found. Run fetch_data.py first.")

        # 计算 20 日均值
        result = Compiler.evaluate(df, "Mean($close, 20)", "ma20")
        assert "ma20" in result.columns
        assert result["ma20"][0] is None  # 前 19 行为 null
        assert result["ma20"][19] is not None

        # 计算收益率
        result = Compiler.evaluate(df, "Return($close, 1)", "ret")
        assert "ret" in result.columns
