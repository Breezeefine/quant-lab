"""AKShare 网关集成测试（标记为 slow，需要网络）"""

from datetime import date

import pytest

from quant_lab.data.akshare_gateway import AKShareGateway
from quant_lab.data.schemas import FetchRequest


@pytest.mark.slow
class TestAKShareGateway:
    def test_fetch_daily(self):
        gateway = AKShareGateway()
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
        gateway = AKShareGateway()
        df = gateway.get_stock_list()

        assert len(df) > 100  # A 股至少有几百只
        assert "symbol" in df.columns
        assert "name" in df.columns
