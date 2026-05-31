"""数据模型测试"""

from datetime import date

from quant_lab.data.schemas import DailyBar, FetchRequest, StockInfo


class TestDailyBar:
    def test_create_daily_bar(self):
        bar = DailyBar(
            date=date(2024, 1, 2),
            open=10.0,
            high=10.5,
            low=9.8,
            close=10.2,
            volume=1000000,
        )
        assert bar.date == date(2024, 1, 2)
        assert bar.open == 10.0
        assert bar.close == 10.2
        assert bar.volume == 1000000

    def test_default_values(self):
        bar = DailyBar(
            date=date(2024, 1, 2),
            open=10.0, high=10.5, low=9.8, close=10.2,
            volume=1000000,
        )
        assert bar.amount == 0.0
        assert bar.turnover == 0.0
        assert bar.pre_close == 0.0


class TestFetchRequest:
    def test_create_request(self):
        req = FetchRequest(
            symbol="600000",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        assert req.symbol == "600000"
        assert req.market == "auto"


class TestStockInfo:
    def test_create_stock_info(self):
        info = StockInfo(
            symbol="600000",
            name="浦发银行",
            market="SH",
        )
        assert info.board == "main"
