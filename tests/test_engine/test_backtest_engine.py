from datetime import date

import polars as pl
import pytest

from quant_lab.engine.core import BacktestEngine
from quant_lab.engine.matching import OrderSide
from quant_lab.strategy.examples.buy_and_hold import BuyAndHoldStrategy
from quant_lab.strategy.examples.dual_moving_average import DualMovingAverageStrategy


def test_backtest_engine_runs_buy_and_hold():
    df = pl.DataFrame({
        "date": [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)],
        "open": [10.0, 11.0, 12.0],
        "high": [10.5, 11.5, 12.5],
        "low": [9.5, 10.5, 11.5],
        "close": [10.0, 11.0, 12.0],
        "volume": [1000, 1000, 1000],
    })

    result = BacktestEngine(initial_capital=10_000.0).run(
        data=df,
        strategy=BuyAndHoldStrategy(symbol="600000", quantity=100),
    )

    assert result.equity_curve.height == 3
    assert result.equity_curve["equity"].to_list() == [10_000.0, 10_100.0, 10_200.0]
    assert len(result.trades) == 1
    assert result.trades[0].price == 10.0
    assert result.metrics["total_return"] == pytest.approx(0.02)


def test_backtest_engine_runs_dual_moving_average_and_records_trades():
    df = pl.DataFrame({
        "date": [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5), date(2024, 1, 8)],
        "open": [10.0, 10.0, 13.0, 10.0, 9.0],
        "high": [10.5, 10.5, 13.5, 10.5, 9.5],
        "low": [9.5, 9.5, 12.5, 9.5, 8.5],
        "close": [10.0, 10.0, 13.0, 10.0, 9.0],
        "volume": [1000, 1000, 1000, 1000, 1000],
    })

    result = BacktestEngine(initial_capital=10_000.0).run(
        data=df,
        strategy=DualMovingAverageStrategy(symbol="600000", short_window=1, long_window=3, quantity=100),
    )

    assert len(result.trades) == 2
    assert result.trades[0].side == OrderSide.BUY
    assert result.trades[0].price == 13.0
    assert result.trades[1].side == OrderSide.SELL
    assert result.trades[1].price == 10.0
    assert result.trades[0].fee == 0.0
