"""买入持有策略"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quant_lab.engine.matching import Order, OrderSide
from quant_lab.engine.portfolio import Portfolio


@dataclass
class BuyAndHoldStrategy:
    symbol: str
    quantity: int
    bought: bool = False

    def on_bar(self, bar: dict[str, Any], portfolio: Portfolio) -> list[Order]:
        if self.bought:
            return []
        self.bought = True
        return [Order(symbol=self.symbol, side=OrderSide.BUY, quantity=self.quantity)]
