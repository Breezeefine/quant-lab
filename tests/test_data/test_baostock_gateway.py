"""Baostock 网关集成测试（需要网络）"""

from datetime import date

import pytest

from quant_lab.data.baostock_gateway import BaostockGateway
from quant_lab.data.schemas import FetchRequest


@pytest.mark.slow
class TestBaostockGateway:
    def test_fetch_daily(self):
        gateway = BaostockGateway()
        request = FetchRequest(
            symbol="600000",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        df = gateway.fetch_daily(request)

        assert len(df) > 0
        assert "date" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns

    def test_get_stock_list(self):
        gateway = BaostockGateway()
        df = gateway.get_stock_list()

        assert len(df) > 100
        assert "symbol" in df.columns
        assert "name" in df.columns
