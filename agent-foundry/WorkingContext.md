# 工作上下文

## 当前位置

- 阶段：切片开发
- 当前任务：S1✅ S2✅ S3✅ S4✅，待进入 S5（A 股规则）
- 架构版本：v2.0（Agent Quant，多 Agent + 记忆 + 反思）
- 最近更新：2026-06-01

## 下个会话必须读取

- AGENTS.md
- agent-foundry/WorkingContext.md
- agent-foundry/Status.md

## 按需读取

- agent-foundry/Product.md v2.0（Agent Quant 架构）
- agent-foundry/Research.md（含 Harness + LLM + Agent Quant 调研）
- agent-foundry/DevPlan.md v2.0（S1-S12 三阶段计划）
- agent-foundry/Progress.md

## 当前进度

| Phase | 切片 | 状态 |
|-------|------|------|
| 1 基础设施 | S1 数据就绪 | ✅ |
| 1 基础设施 | S2 因子计算 | ✅ |
| 1 基础设施 | S3 第一次回测 | ✅ |
| 1 基础设施 | S4 真实策略 | ✅ |
| 1 基础设施 | S5 A 股规则 | 待开发 |
| 1 基础设施 | S6 模拟实盘 | 待开发 |
| 1 基础设施 | S7 可视化 | 待开发 |
| 2 情绪数据 | S8 情绪数据采集 | 待开发 |
| 2 情绪数据 | S9 情绪指标引擎 | 待开发 |
| 3 Agent | S10 Agent 框架 | 待开发 |
| 3 Agent | S11 退学炒股策略 | 待开发 |
| 3 Agent | S12 报告与进化 | 待开发 |

## 最近调研摘要

- 2026-06-01 S4 真实策略完成：新增基础费用模型、限价单撮合、费用净现金流和双均线策略；S4 聚合测试 19 passed，非 slow 回归 77 passed, 5 deselected。
- 2026-06-01 全需求数据源覆盖验证：`scripts/verify_data_requirements.py` 覆盖 13 类必需能力，23 项检查中 22 项通过；1 项东方财富人气榜失败但社交/热度已有百度热搜+微博股票报告替代，missing_capabilities=[]。
- 2026-06-01 AKShare/东方财富专项调研：情绪数据不能硬依赖 AKShare 单源；S8 应实现 SentimentProvider fallback 链（AKShare → 直接东方财富 → curl_cffi 可选 → Tushare Pro）。
- 2026-06-01 S3 第一次回测完成：S3 测试 6/6 passed；非 slow 回归 63 passed, 5 deselected。

## 下一步

进入 S5 开发：A 股规则（T+1 / 涨跌停 / 手续费细化 / 最小交易单位）

## 关键文件（S1-S2 已完成）

- src/quant_lab/expression/parser.py — DSL 解析器
- src/quant_lab/expression/compiler.py — AST→Polars 编译器
- src/quant_lab/expression/operators.py — 20 个运算符
- src/quant_lab/data/baostock_gateway.py — Baostock 数据源
- src/quant_lab/data/storage.py — Parquet 存储
- tests/ — 非 slow 回归 77 passed，S4 聚合测试 19 passed
- src/quant_lab/engine/ — S3 回测引擎、撮合、持仓
- src/quant_lab/analytics/metrics.py — S3 绩效指标
- src/quant_lab/strategy/examples/buy_and_hold.py — S3 买入持有策略
- src/quant_lab/engine/fees.py — S4 基础费用模型
- src/quant_lab/strategy/examples/dual_moving_average.py — S4 双均线策略
