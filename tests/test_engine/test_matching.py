import pytest

from quant_lab.engine.fees import BasicFeeModel
from quant_lab.engine.matching import MatchingEngine, Order, OrderSide


def test_close_price_matching_creates_trade():
    bar = {
        "date": "2024-01-02",
        "close": 10.0,
    }
    order = Order(symbol="600000", side=OrderSide.BUY, quantity=100)

    trade = MatchingEngine().match(order, bar)

    assert trade.symbol == "600000"
    assert trade.side == OrderSide.BUY
    assert trade.quantity == 100
    assert trade.price == 10.0
    assert trade.amount == 1000.0
    assert trade.date == "2024-01-02"


def test_matching_rejects_non_positive_quantity():
    bar = {"date": "2024-01-02", "close": 10.0}
    order = Order(symbol="600000", side=OrderSide.BUY, quantity=0)

    trade = MatchingEngine().match(order, bar)

    assert trade is None


def test_buy_limit_order_fills_when_low_reaches_limit():
    bar = {"date": "2024-01-02", "low": 9.8, "high": 10.5, "close": 10.2}
    order = Order(symbol="600000", side=OrderSide.BUY, quantity=100, limit_price=10.0)

    trade = MatchingEngine().match(order, bar)

    assert trade.price == 10.0


def test_buy_limit_order_does_not_fill_when_low_stays_above_limit():
    bar = {"date": "2024-01-02", "low": 10.1, "high": 10.5, "close": 10.2}
    order = Order(symbol="600000", side=OrderSide.BUY, quantity=100, limit_price=10.0)

    trade = MatchingEngine().match(order, bar)

    assert trade is None


def test_sell_limit_order_fills_when_high_reaches_limit():
    bar = {"date": "2024-01-02", "low": 9.8, "high": 10.5, "close": 10.2}
    order = Order(symbol="600000", side=OrderSide.SELL, quantity=100, limit_price=10.4)

    trade = MatchingEngine().match(order, bar)

    assert trade.price == 10.4


def test_market_order_still_fills_at_close_price():
    bar = {"date": "2024-01-02", "low": 9.0, "high": 12.0, "close": 11.0}
    order = Order(symbol="600000", side=OrderSide.BUY, quantity=100)

    trade = MatchingEngine().match(order, bar)

    assert trade.price == 11.0


def test_matching_attaches_fee_components_to_trade():
    bar = {"date": "2024-01-02", "close": 10_000.0}
    order = Order(symbol="600000", side=OrderSide.SELL, quantity=10)

    trade = MatchingEngine(fee_model=BasicFeeModel()).match(order, bar)

    assert trade.commission == pytest.approx(25.0)
    assert trade.stamp_tax == pytest.approx(100.0)
    assert trade.transfer_fee == pytest.approx(2.0)
    assert trade.fee == pytest.approx(127.0)
