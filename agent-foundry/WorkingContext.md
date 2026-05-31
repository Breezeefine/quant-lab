# 工作上下文

## 当前位置

- 阶段：切片开发
- 当前任务：S1 完成，待进入 S2 因子计算
- 最近更新：2026-05-31

## 下个会话必须读取

- AGENTS.md
- agent-foundry/WorkingContext.md
- agent-foundry/Status.md

## 按需读取

- agent-foundry/Product.md
- agent-foundry/Research.md
- agent-foundry/DevPlan.md
- agent-foundry/Progress.md
- agent-foundry/Decisions.md
- agent-foundry/Memory.md

## 仅排查历史时读取

- agent-foundry/Reflection.md
- agent-foundry/Feedback.md

## 最近调研摘要

- 2026-05-31 完成四维并行调研 + 三路聚焦深潜
- 推荐方案：uv + Python 3.12 + Polars/DuckDB + Parquet + Streamlit + 自建回测引擎
- 数据源：AKShare（免费、零注册、覆盖广）
- 表达式引擎：基于 Polars 自建，移植 qlib DSL 模式，约 1000-1500 行
- Gateway 模式：采用 vnpy 抽象工厂 + 事件驱动，AKShareGateway + SimBrokerGateway
- 模拟实盘：统一引擎设计，回测和模拟实盘共用策略代码
- MVP 范围扩展至约 4000 行代码
- 详见 agent-foundry/Research.md

## 最近审查摘要

- 2026-05-31 产品审查通过（修正 3 项：目标用户、一句话定义、DSL 信号规则）
- 2026-05-31 计划审查通过（7 个垂直切片 S1-S7，独立可验证，依赖关系清晰）

## 最近复盘摘要

- 无。

## 未决问题

- AKShare 集成测试因网络问题失败，需在有网络环境下重试验证。
