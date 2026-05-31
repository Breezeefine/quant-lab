"""全局配置"""

from pathlib import Path

from pydantic import BaseModel


class Config(BaseModel):
    """全局配置"""

    # 数据目录
    data_dir: Path = Path("data")

    # 原始数据路径
    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    # 回测结果路径
    @property
    def backtest_dir(self) -> Path:
        return self.data_dir / "backtest"

    # A 股交易规则
    commission_rate: float = 0.00025  # 佣金费率万 2.5
    commission_min: float = 5.0  # 最低佣金 5 元
    stamp_tax_rate: float = 0.001  # 印花税千 1（仅卖出）
    transfer_fee_rate: float = 0.00002  # 过户费十万分之二

    # 默认回测参数
    initial_capital: float = 1_000_000.0  # 初始资金 100 万

    # 滑点
    slippage_rate: float = 0.001  # 滑点 0.1%


# 全局配置实例
settings = Config()
