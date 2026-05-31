from __future__ import annotations

from dataclasses import dataclass

from quant_lab.config import settings
from quant_lab.engine.matching import OrderSide


@dataclass(frozen=True)
class Fee:
    commission: float
    stamp_tax: float
    transfer_fee: float

    @property
    def total(self) -> float:
        return self.commission + self.stamp_tax + self.transfer_fee


@dataclass(frozen=True)
class BasicFeeModel:
    commission_rate: float = settings.commission_rate
    commission_min: float = settings.commission_min
    stamp_tax_rate: float = settings.stamp_tax_rate
    transfer_fee_rate: float = settings.transfer_fee_rate

    def calculate(self, side: OrderSide, amount: float) -> Fee:
        if amount <= 0:
            return Fee(commission=0.0, stamp_tax=0.0, transfer_fee=0.0)

        commission = max(amount * self.commission_rate, self.commission_min)
        stamp_tax = amount * self.stamp_tax_rate if side == OrderSide.SELL else 0.0
        transfer_fee = amount * self.transfer_fee_rate
        return Fee(
            commission=float(commission),
            stamp_tax=float(stamp_tax),
            transfer_fee=float(transfer_fee),
        )
