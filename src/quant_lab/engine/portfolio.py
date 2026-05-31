"""持仓与资金管理"""

from __future__ import annotations

from dataclasses import dataclass, field

from .matching import OrderSide, Trade


@dataclass
class Portfolio:
    initial_cash: float
    cash: float | None = None
    positions: dict[str, int] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.cash is None:
            self.cash = self.initial_cash

    def apply_trade(self, trade: Trade) -> None:
        if trade.side == OrderSide.BUY:
            self.cash -= trade.amount + trade.fee
            self.positions[trade.symbol] = self.position(trade.symbol) + trade.quantity
        else:
            self.cash += trade.amount - trade.fee
            self.positions[trade.symbol] = self.position(trade.symbol) - trade.quantity
        self.trades.append(trade)

    def position(self, symbol: str) -> int:
        return self.positions.get(symbol, 0)

    def equity(self, prices: dict[str, float]) -> float:
        position_value = sum(quantity * prices.get(symbol, 0.0) for symbol, quantity in self.positions.items())
        return float(self.cash + position_value)
