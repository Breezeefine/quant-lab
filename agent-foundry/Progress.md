# 进度

## 切片进度

| 切片 | 名称 | Phase | 状态 | 最近验证 | 备注 |
|------|------|-------|------|----------|------|
| S1 | 数据就绪 | 1 | ✅ 完成 | 2026-05-31 | 10/10 测试通过 |
| S2 | 因子计算 | 1 | ✅ 完成 | 2026-05-31 | 47/47 测试通过，20 运算符 |
| S3 | 第一次回测 | 1 | ✅ 完成 | 2026-06-01 | 引擎核心 + 撮合 + 买入持有；6/6 S3 测试通过 |
| S4 | 真实策略 | 1 | ✅ 完成 | 2026-06-01 | 双均线 + 限价单撮合 + 基础手续费；19/19 S4 测试通过 |
| S5 | A 股规则 | 1 | 待开发 | — | T+1/涨跌停/手续费 |
| S6 | 模拟实盘 | 1 | 待开发 | — | 统一引擎 + 腾讯行情 |
| S7 | 可视化 | 1 | 待开发 | — | Streamlit 5 页面 |
| S8 | 情绪数据 | 2 | 待开发 | — | 涨停池/炸板池/龙虎榜 |
| S9 | 情绪指标 | 2 | 待开发 | — | 连板高度/炸板率/情绪温度 |
| S10 | Agent 框架 | 3 | 待开发 | — | 多 Agent + 记忆 + LLM |
| S11 | 退学炒股策略 | 3 | 待开发 | — | 龙头识别 + 情绪择时 |
| S12 | 报告与进化 | 3 | 待开发 | — | 每日报告 + 反思循环 |

## 架构决策记录

### 2026-05-31：Agent Quant 架构重设计
- 用户目标：量化"退学炒股"策略（打板/龙头/情绪周期）
- 调研结论：采用 Agent Quant 模式（参考 TradingAgents 81k stars）
- 核心设计：Agent 扫描推荐 → 人类判断决策 → Agent 从结果学习
- LLM：用户自备 API Key（DeepSeek/Qwen/Claude），LiteLLM 统一调用
- 方案：S1-S7 不变，新增 S8-S12 覆盖情绪数据 + Agent 系统

## S3 验证记录（2026-06-01）

- RED：`uv run pytest tests/test_engine/ -v` → 4 个 collection errors，原因是 `quant_lab.engine` / `quant_lab.analytics` 尚不存在，符合预期。
- GREEN：新增最小回测闭环后，`uv run pytest tests/test_engine/ -v` → 6 passed。
- 回归：`uv run pytest tests/test_data/ tests/test_expression/ tests/test_engine/ -v -m "not slow"` → 63 passed, 5 deselected。
- 未覆盖：slow 网络集成测试未纳入通过门禁；直接运行包含 AKShare slow 测试时，已知东方财富接口会断连失败。
- 变更文件：新增 `src/quant_lab/engine/`、`src/quant_lab/analytics/`、`src/quant_lab/strategy/`、`tests/test_engine/`。

## S4 验证记录（2026-06-01）

- RED：`uv run pytest tests/test_engine/test_fees.py -v` → 1 collection error，原因是 `quant_lab.engine.fees` 尚不存在，符合预期。
- RED：`uv run pytest tests/test_engine/test_portfolio.py -v` → 2 failed，原因是 `Trade` 尚无费用字段，符合预期。
- RED：`uv run pytest tests/test_engine/test_matching.py -v` → 4 failed，原因是限价单逻辑和 `fee_model` 注入尚不存在，符合预期。
- RED：`uv run pytest tests/test_strategy/test_dual_moving_average.py -v` → 1 collection error，原因是双均线策略模块尚不存在，符合预期。
- GREEN：`uv run pytest tests/test_engine/test_fees.py tests/test_engine/test_matching.py tests/test_engine/test_portfolio.py tests/test_strategy/test_dual_moving_average.py tests/test_engine/test_backtest_engine.py -v` → 19 passed。
- 回归：`uv run pytest tests/test_data/ tests/test_expression/ tests/test_engine/ tests/test_strategy/ -v -m "not slow"` → 77 passed, 5 deselected。
- 变更文件：新增 `src/quant_lab/engine/fees.py`、`src/quant_lab/strategy/examples/dual_moving_average.py`、`tests/test_engine/test_fees.py`、`tests/test_strategy/test_dual_moving_average.py`；修改 `matching.py`、`portfolio.py`、`engine/__init__.py`、`strategy/examples/__init__.py`、相关 S4 测试。

## 数据源验证记录（2026-06-01）

- 命令：`uv run python scripts/verify_data_requirements.py`
- 结果：23 checks, 22 passed, 1 optional failed；13 required capabilities 全部覆盖，`missing_capabilities=[]`。
- 已覆盖能力：涨停生态、龙虎榜、题材/板块、板块强度/资金替代、题材驱动事件、板块异动/主力净流入替代、社交/热度、新闻、公告、研报、宏观新闻、北向资金、实时行情。
- 剩余单源失败：东方财富人气榜 `stock_hot_rank_em` 断连，但社交/热度已有百度热搜股票和微博股票报告两路替代。
- 结论：S8 可基于“能力 provider”开发，不强依赖单个失败接口。

## 阻塞

- 无。
