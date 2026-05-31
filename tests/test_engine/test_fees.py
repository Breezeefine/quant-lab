import pytest

from quant_lab.engine.fees import BasicFeeModel
from quant_lab.engine.matching import OrderSide


def test_basic_fee_model_applies_minimum_commission_on_buy():
    fee = BasicFeeModel().calculate(side=OrderSide.BUY, amount=1_000.0)

    assert fee.commission == 5.0
    assert fee.stamp_tax == 0.0
    assert fee.transfer_fee == pytest.approx(0.02)
    assert fee.total == pytest.approx(5.02)


def test_basic_fee_model_applies_stamp_tax_only_on_sell():
    fee = BasicFeeModel().calculate(side=OrderSide.SELL, amount=100_000.0)

    assert fee.commission == pytest.approx(25.0)
    assert fee.stamp_tax == pytest.approx(100.0)
    assert fee.transfer_fee == pytest.approx(2.0)
    assert fee.total == pytest.approx(127.0)


def test_basic_fee_model_keeps_components_separate():
    fee = BasicFeeModel(commission_rate=0.001, commission_min=1.0, stamp_tax_rate=0.002, transfer_fee_rate=0.003).calculate(
        side=OrderSide.SELL,
        amount=10_000.0,
    )

    assert fee.commission == pytest.approx(10.0)
    assert fee.stamp_tax == pytest.approx(20.0)
    assert fee.transfer_fee == pytest.approx(30.0)
    assert fee.total == pytest.approx(60.0)
