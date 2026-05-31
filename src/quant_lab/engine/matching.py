"""撮合引擎"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class Order:
    symbol: str
    side: OrderSide
    quantity: int
    limit_price: float | None = None


@dataclass(frozen=True)
class Trade:
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    date: Any
    commission: float = 0.0
    stamp_tax: float = 0.0
    transfer_fee: float = 0.0

    @property
    def amount(self) -> float:
        return self.quantity * self.price

    @property
    def fee(self) -> float:
        return self.commission + self.stamp_tax + self.transfer_fee


class MatchingEngine:
    def __init__(self, price_field: str = "close", fee_model: Any | None = None):
        self.price_field = price_field
        self.fee_model = fee_model

    def match(self, order: Order, bar: dict[str, Any]) -> Trade | None:
        if order.quantity <= 0:
            return None

        price = self._match_price(order, bar)
        if price is None:
            return None

        amount = order.quantity * price
        fee = self.fee_model.calculate(order.side, amount) if self.fee_model is not None else None
        return Trade(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=price,
            date=bar.get("date"),
            commission=fee.commission if fee is not None else 0.0,
            stamp_tax=fee.stamp_tax if fee is not None else 0.0,
            transfer_fee=fee.transfer_fee if fee is not None else 0.0,
        )

    def _match_price(self, order: Order, bar: dict[str, Any]) -> float | None:
        if order.limit_price is None:
            if self.price_field not in bar:
                raise KeyError(f"bar missing price field: {self.price_field}")
            return float(bar[self.price_field])

        if order.side == OrderSide.BUY:
            if "low" not in bar:
                raise KeyError("bar missing price field: low")
            return float(order.limit_price) if float(bar["low"]) <= order.limit_price else None

        if "high" not in bar:
            raise KeyError("bar missing price field: high")
        return float(order.limit_price) if float(bar["high"]) >= order.limit_price else None
