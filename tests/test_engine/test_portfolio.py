from quant_lab.engine.matching import OrderSide, Trade
from quant_lab.engine.portfolio import Portfolio


def test_portfolio_updates_cash_and_position_after_buy():
    portfolio = Portfolio(initial_cash=10_000.0)
    trade = Trade(
        symbol="600000",
        side=OrderSide.BUY,
        quantity=100,
        price=10.0,
        date="2024-01-02",
    )

    portfolio.apply_trade(trade)

    assert portfolio.cash == 9_000.0
    assert portfolio.position("600000") == 100
    assert len(portfolio.trades) == 1


def test_portfolio_buy_reduces_cash_by_amount_plus_fees():
    portfolio = Portfolio(initial_cash=10_000.0)
    trade = Trade(
        symbol="600000",
        side=OrderSide.BUY,
        quantity=100,
        price=10.0,
        date="2024-01-02",
        commission=5.0,
        transfer_fee=0.02,
    )

    portfolio.apply_trade(trade)

    assert portfolio.cash == 8_994.98
    assert portfolio.position("600000") == 100


def test_portfolio_sell_increases_cash_by_amount_minus_fees():
    portfolio = Portfolio(initial_cash=10_000.0)
    trade = Trade(
        symbol="600000",
        side=OrderSide.SELL,
        quantity=100,
        price=10.0,
        date="2024-01-02",
        commission=5.0,
        stamp_tax=1.0,
        transfer_fee=0.02,
    )

    portfolio.apply_trade(trade)

    assert portfolio.cash == 10_993.98
    assert portfolio.position("600000") == -100


def test_portfolio_equity_marks_position_to_market():
    portfolio = Portfolio(initial_cash=10_000.0)
    portfolio.apply_trade(Trade("600000", OrderSide.BUY, 100, 10.0, "2024-01-02"))

    equity = portfolio.equity({"600000": 12.0})

    assert equity == 10_200.0
