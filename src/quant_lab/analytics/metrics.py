"""绩效指标"""

from __future__ import annotations

import math

import polars as pl


def calculate_metrics(equity_curve: pl.DataFrame, initial_capital: float) -> dict[str, float]:
    if equity_curve.is_empty():
        return {"total_return": 0.0, "max_drawdown": 0.0, "sharpe_ratio": 0.0}

    equity = [float(value) for value in equity_curve["equity"].to_list()]
    total_return = equity[-1] / initial_capital - 1

    peak = equity[0]
    max_drawdown = 0.0
    for value in equity:
        peak = max(peak, value)
        drawdown = value / peak - 1
        max_drawdown = min(max_drawdown, drawdown)

    returns = []
    for prev, curr in zip(equity, equity[1:]):
        if prev != 0:
            returns.append(curr / prev - 1)

    sharpe_ratio = 0.0
    if returns:
        mean_return = sum(returns) / len(returns)
        variance = sum((ret - mean_return) ** 2 for ret in returns) / len(returns)
        std_return = math.sqrt(variance)
        if std_return > 0:
            sharpe_ratio = mean_return / std_return * math.sqrt(252)

    return {
        "total_return": float(total_return),
        "max_drawdown": float(max_drawdown),
        "sharpe_ratio": float(sharpe_ratio),
    }
