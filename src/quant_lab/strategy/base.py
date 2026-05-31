"""策略基类"""

from __future__ import annotations

from typing import Any, Protocol

from quant_lab.engine.matching import Order
from quant_lab.engine.portfolio import Portfolio


class StrategyBase(Protocol):
    def on_bar(self, bar: dict[str, Any], portfolio: Portfolio) -> list[Order]:
        ...
