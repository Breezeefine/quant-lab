from quant_lab.engine.matching import OrderSide
from quant_lab.engine.portfolio import Portfolio
from quant_lab.strategy.examples.dual_moving_average import DualMovingAverageStrategy


def test_dual_moving_average_waits_for_long_window():
    strategy = DualMovingAverageStrategy(symbol="600000", short_window=2, long_window=3, quantity=100)
    portfolio = Portfolio(initial_cash=10_000.0)

    assert strategy.on_bar({"close": 10.0}, portfolio) == []
    assert strategy.on_bar({"close": 11.0}, portfolio) == []


def test_dual_moving_average_buys_when_short_average_above_long_average():
    strategy = DualMovingAverageStrategy(symbol="600000", short_window=2, long_window=3, quantity=100)
    portfolio = Portfolio(initial_cash=10_000.0)

    strategy.on_bar({"close": 10.0}, portfolio)
    strategy.on_bar({"close": 10.0}, portfolio)
    orders = strategy.on_bar({"close": 13.0}, portfolio)

    assert len(orders) == 1
    assert orders[0].side == OrderSide.BUY
    assert orders[0].quantity == 100


def test_dual_moving_average_sells_existing_position_when_short_average_below_long_average():
    strategy = DualMovingAverageStrategy(symbol="600000", short_window=2, long_window=3, quantity=100)
    portfolio = Portfolio(initial_cash=10_000.0, positions={"600000": 100})

    strategy.on_bar({"close": 13.0}, portfolio)
    strategy.on_bar({"close": 13.0}, portfolio)
    orders = strategy.on_bar({"close": 10.0}, portfolio)

    assert len(orders) == 1
    assert orders[0].side == OrderSide.SELL
    assert orders[0].quantity == 100
