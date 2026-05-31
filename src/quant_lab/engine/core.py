"""回测引擎核心"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

from quant_lab.analytics.metrics import calculate_metrics
from quant_lab.config import settings
from quant_lab.engine.matching import MatchingEngine, Trade
from quant_lab.engine.portfolio import Portfolio
from quant_lab.strategy.base import StrategyBase


@dataclass(frozen=True)
class BacktestResult:
    equity_curve: pl.DataFrame
    trades: list[Trade]
    metrics: dict[str, float]


class BacktestEngine:
    def __init__(self, initial_capital: float | None = None, matching: MatchingEngine | None = None):
        self.initial_capital = initial_capital or settings.initial_capital
        self.matching = matching or MatchingEngine()

    def run(self, data: pl.DataFrame, strategy: StrategyBase) -> BacktestResult:
        portfolio = Portfolio(initial_cash=self.initial_capital)
        equity_rows: list[dict[str, Any]] = []

        for bar in data.sort("date").iter_rows(named=True):
            for order in strategy.on_bar(bar, portfolio):
                trade = self.matching.match(order, bar)
                if trade is not None:
                    portfolio.apply_trade(trade)

            prices = self._mark_prices(bar, portfolio)
            equity_rows.append({
                "date": bar.get("date"),
                "equity": portfolio.equity(prices),
                "cash": float(portfolio.cash),
            })

        equity_curve = pl.DataFrame(equity_rows)
        metrics = calculate_metrics(equity_curve, self.initial_capital)
        return BacktestResult(
            equity_curve=equity_curve,
            trades=list(portfolio.trades),
            metrics=metrics,
        )

    def _mark_prices(self, bar: dict[str, Any], portfolio: Portfolio) -> dict[str, float]:
        return {symbol: float(bar["close"]) for symbol in portfolio.positions}
