"""数据采集脚本

用法：
    uv run python scripts/fetch_data.py --symbol 600000 --start 2024-01-01 --end 2024-12-31
    uv run python scripts/fetch_data.py --symbol 600000  # 默认最近 1 年
"""

import argparse
from datetime import date, timedelta

from loguru import logger

from quant_lab.data.akshare_gateway import AKShareGateway
from quant_lab.data.schemas import FetchRequest
from quant_lab.data.storage import Storage


def main():
    parser = argparse.ArgumentParser(description="A 股数据采集")
    parser.add_argument("--symbol", required=True, help="股票代码（如 600000）")
    parser.add_argument("--start", help="开始日期（YYYY-MM-DD），默认 1 年前")
    parser.add_argument("--end", help="结束日期（YYYY-MM-DD），默认今天")
    parser.add_argument("--market", default="auto", help="市场：SH/SZ/auto")
    args = parser.parse_args()

    # 默认日期
    end_date = date.fromisoformat(args.end) if args.end else date.today()
    start_date = (
        date.fromisoformat(args.start) if args.start
        else end_date - timedelta(days=365)
    )

    # 自动判断市场
    market = args.market
    if market == "auto":
        market = "SH" if args.symbol.startswith("6") else "SZ"

    logger.info(f"Fetching {market}{args.symbol} from {start_date} to {end_date}")

    # 采集数据
    gateway = AKShareGateway()
    request = FetchRequest(
        symbol=args.symbol,
        start_date=start_date,
        end_date=end_date,
        market=market,
    )
    df = gateway.fetch_daily(request)

    # 保存数据
    storage = Storage()
    path = storage.save_daily(df, args.symbol, market)

    # 输出摘要
    summary = storage.get_summary(args.symbol, market)
    print("\n" + "=" * 50)
    print(f"数据采集完成：{market}{args.symbol}")
    print("=" * 50)
    print(f"  数据行数：{summary['rows']}")
    if "date_range" in summary:
        print(f"  日期范围：{summary['date_range'][0]} ~ {summary['date_range'][1]}")
    if "latest_close" in summary:
        print(f"  最新收盘：{summary['latest_close']:.2f}")
    print(f"  存储路径：{path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
