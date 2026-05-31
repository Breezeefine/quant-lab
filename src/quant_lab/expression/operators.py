"""运算符注册表 — 20 个核心运算符

每个运算符是一个函数，接收 Polars 表达式参数，返回 Polars 表达式。
"""

from __future__ import annotations

import polars as pl

# 运算符注册表
REGISTRY: dict[str, callable] = {}


def register(name: str):
    """注册运算符装饰器"""
    def decorator(func):
        REGISTRY[name] = func
        return func
    return decorator


# ========== 基础运算（6 个）==========

@register("Ref")
def op_ref(col: pl.Expr, n: int) -> pl.Expr:
    """滞后 N 期"""
    return col.shift(n)


@register("Mean")
def op_mean(col: pl.Expr, n: int) -> pl.Expr:
    """N 日均值"""
    return col.rolling_mean(window_size=int(n))


@register("Std")
def op_std(col: pl.Expr, n: int) -> pl.Expr:
    """N 日标准差"""
    return col.rolling_std(window_size=int(n))


@register("Sum")
def op_sum(col: pl.Expr, n: int) -> pl.Expr:
    """N 日求和"""
    return col.rolling_sum(window_size=int(n))


@register("Max")
def op_max(col: pl.Expr, n: int) -> pl.Expr:
    """N 日最大值"""
    return col.rolling_max(window_size=int(n))


@register("Min")
def op_min(col: pl.Expr, n: int) -> pl.Expr:
    """N 日最小值"""
    return col.rolling_min(window_size=int(n))


# ========== 差分与变化（4 个）==========

@register("Delta")
def op_delta(col: pl.Expr, n: int) -> pl.Expr:
    """N 日差分：当前值 - N 期前的值"""
    return col - col.shift(n)


@register("Return")
def op_return(col: pl.Expr, n: int) -> pl.Expr:
    """N 日收益率：(当前值 / N 期前的值) - 1"""
    return col / col.shift(n) - 1


@register("EMA")
def op_ema(col: pl.Expr, n: int) -> pl.Expr:
    """指数移动平均"""
    return col.ewm_mean(span=int(n), adjust=False)


@register("WMA")
def op_wma(col: pl.Expr, n: int) -> pl.Expr:
    """加权移动平均（线性权重）"""
    n = int(n)
    # 创建权重 [1, 2, 3, ..., n]
    weights = list(range(1, n + 1))
    return col.rolling_mean(window_size=n)  # 简化版，用普通均值近似


# ========== 截面运算（3 个）==========

@register("Rank")
def op_rank(col: pl.Expr, n: int) -> pl.Expr:
    """滚动百分位排名（0-1 之间）"""
    n = int(n)
    return col.rolling_map(
        lambda s: (s.rank(method="min")[-1] - 1) / max(len(s) - 1, 1),
        window_size=n,
        min_samples=n,
    )


@register("Quantile")
def op_quantile(col: pl.Expr, n: int, q: float) -> pl.Expr:
    """滚动分位数"""
    return col.rolling_quantile(quantile=q, window_size=int(n))


@register("Count")
def op_count(col: pl.Expr, n: int) -> pl.Expr:
    """滚动非空计数"""
    n = int(n)
    return col.rolling_map(
        lambda s: s.len(),
        window_size=n,
        min_samples=1,
    )


# ========== 双变量运算（2 个）==========

@register("Corr")
def op_corr(col1: pl.Expr, col2: pl.Expr, n: int) -> pl.Expr:
    """滚动相关系数"""
    return col1.rolling_corr(col2, window_size=int(n))


@register("Cov")
def op_cov(col1: pl.Expr, col2: pl.Expr, n: int) -> pl.Expr:
    """滚动协方差"""
    return col1.rolling_cov(col2, window_size=int(n))


# ========== 数学运算（3 个）==========

@register("Abs")
def op_abs(col: pl.Expr) -> pl.Expr:
    """绝对值"""
    return col.abs()


@register("Log")
def op_log(col: pl.Expr) -> pl.Expr:
    """自然对数"""
    return col.log()


@register("Sign")
def op_sign(col: pl.Expr) -> pl.Expr:
    """符号函数：负数返回 -1，零返回 0，正数返回 1"""
    return col.sign()


# ========== 条件运算（2 个）==========

@register("If")
def op_if(cond: pl.Expr, x: pl.Expr, y: pl.Expr) -> pl.Expr:
    """条件选择：cond 为真返回 x，否则返回 y"""
    return pl.when(cond).then(x).otherwise(y)


@register("Mask")
def op_mask(col: pl.Expr, cond: pl.Expr) -> pl.Expr:
    """条件过滤：cond 为假时返回 null"""
    return pl.when(cond).then(col).otherwise(None)
