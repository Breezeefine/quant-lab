from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quant_lab.engine.matching import Order, OrderSide
from quant_lab.engine.portfolio import Portfolio


@dataclass
class DualMovingAverageStrategy:
    symbol: str
    short_window: int
    long_window: int
    quantity: int
    price_field: str = "close"
    prices: list[float] = field(default_factory=list)

    def on_bar(self, bar: dict[str, Any], portfolio: Portfolio) -> list[Order]:
        self.prices.append(float(bar[self.price_field]))
        if len(self.prices) < self.long_window:
            return []

        short_ma = sum(self.prices[-self.short_window:]) / self.short_window
        long_ma = sum(self.prices[-self.long_window:]) / self.long_window
        position = portfolio.position(self.symbol)

        if short_ma > long_ma and position <= 0:
            return [Order(symbol=self.symbol, side=OrderSide.BUY, quantity=self.quantity)]
        if short_ma < long_ma and position > 0:
            return [Order(symbol=self.symbol, side=OrderSide.SELL, quantity=position)]
        return []
