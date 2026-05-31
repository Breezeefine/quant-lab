import polars as pl
import pytest

from quant_lab.analytics.metrics import calculate_metrics


def test_calculate_metrics_from_equity_curve():
    equity_curve = pl.DataFrame({
        "date": ["2024-01-02", "2024-01-03", "2024-01-04"],
        "equity": [10_000.0, 11_000.0, 10_500.0],
    })

    metrics = calculate_metrics(equity_curve, initial_capital=10_000.0)

    assert metrics["total_return"] == pytest.approx(0.05)
    assert metrics["max_drawdown"] == pytest.approx(-500.0 / 11_000.0)
    assert "sharpe_ratio" in metrics
