"""编译器测试 — 用真实数据验证"""

import polars as pl
import pytest

from quant_lab.expression.compiler import Compiler, CompilerError
from quant_lab.expression.parser import Parser


@pytest.fixture
def sample_df():
    """创建测试数据"""
    return pl.DataFrame({
        "close": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0,
                  20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0],
        "open": [9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5,
                 19.5, 20.5, 21.5, 22.5, 23.5, 24.5, 25.5, 26.5, 27.5, 28.5],
        "volume": [1000] * 20,
    })


class TestCompiler:
    def test_feature_reference(self, sample_df):
        result = Compiler.evaluate(sample_df, "$close", "f")
        assert result["f"].to_list() == sample_df["close"].to_list()

    def test_mean(self, sample_df):
        result = Compiler.evaluate(sample_df, "Mean($close, 5)", "ma5")
        values = result["ma5"].to_list()
        # 前 4 个为 null
        assert values[:4] == [None, None, None, None]
        # 第 5 个 = mean(10,11,12,13,14) = 12.0
        assert abs(values[4] - 12.0) < 1e-10

    def test_std(self, sample_df):
        result = Compiler.evaluate(sample_df, "Std($close, 5)", "std5")
        values = result["std5"].to_list()
        assert values[:4] == [None, None, None, None]
        assert values[4] is not None

    def test_ref(self, sample_df):
        result = Compiler.evaluate(sample_df, "Ref($close, 1)", "prev")
        values = result["prev"].to_list()
        assert values[0] is None  # 第一个没有前值
        assert abs(values[1] - 10.0) < 1e-10

    def test_delta(self, sample_df):
        result = Compiler.evaluate(sample_df, "Delta($close, 1)", "d")
        values = result["d"].to_list()
        assert values[0] is None
        assert abs(values[1] - 1.0) < 1e-10  # 11 - 10 = 1

    def test_return(self, sample_df):
        result = Compiler.evaluate(sample_df, "Return($close, 1)", "ret")
        values = result["ret"].to_list()
        assert values[0] is None
        assert abs(values[1] - 0.1) < 1e-10  # (11/10) - 1 = 0.1

    def test_arithmetic(self, sample_df):
        result = Compiler.evaluate(sample_df, "$close + 1", "plus1")
        assert result["plus1"].to_list() == [11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0,
                                              21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0]

    def test_complex_expr(self, sample_df):
        result = Compiler.evaluate(sample_df, "Mean($close, 5) - Mean($close, 10)", "diff")
        # 5日均值和10日均值的差
        values = result["diff"].to_list()
        assert values[:9] == [None] * 9  # 需要至少10个数据点

    def test_nested_call(self, sample_df):
        result = Compiler.evaluate(sample_df, "Rank(Mean($close, 5), 10)", "rank")
        values = result["rank"].to_list()
        # 需要至少 10 个数据点
        assert len(values) == 20

    def test_comparison(self, sample_df):
        result = Compiler.evaluate(sample_df, "$close > 15", "gt15")
        values = result["gt15"].to_list()
        assert values[0] == False  # 10 > 15 = False
        assert values[5] == False  # 15 > 15 = False
        assert values[6] == True   # 16 > 15 = True

    def test_unknown_function(self, sample_df):
        with pytest.raises(CompilerError, match="Unknown function"):
            Compiler.evaluate(sample_df, "Foo($close)", "f")

    def test_sum(self, sample_df):
        result = Compiler.evaluate(sample_df, "Sum($close, 3)", "s")
        values = result["s"].to_list()
        assert values[:2] == [None, None]
        assert abs(values[2] - 33.0) < 1e-10  # 10+11+12 = 33

    def test_max_min(self, sample_df):
        result = Compiler.evaluate(sample_df, "Max($close, 3)", "mx")
        values = result["mx"].to_list()
        assert values[2] == 12.0  # max(10,11,12) = 12

        result = Compiler.evaluate(sample_df, "Min($close, 3)", "mn")
        values = result["mn"].to_list()
        assert values[2] == 10.0  # min(10,11,12) = 10

    def test_ema(self, sample_df):
        result = Compiler.evaluate(sample_df, "EMA($close, 5)", "ema")
        values = result["ema"].to_list()
        assert values[0] is not None  # EMA 从第一个值开始
        assert len(values) == 20

    def test_abs(self, sample_df):
        neg_df = pl.DataFrame({"close": [-1.0, -2.0, 3.0]})
        result = Compiler.evaluate(neg_df, "Abs($close)", "a")
        assert result["a"].to_list() == [1.0, 2.0, 3.0]

    def test_sign(self, sample_df):
        neg_df = pl.DataFrame({"close": [-1.0, 0.0, 3.0]})
        result = Compiler.evaluate(neg_df, "Sign($close)", "s")
        assert result["s"].to_list() == [-1.0, 0.0, 1.0]
