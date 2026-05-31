# Agent Foundry 状态

更新时间：2026-06-01

## 位置

- 阶段：切片开发
- 架构版本：v2.0（Agent Quant）
- 当前切片：S1✅ S2✅ S3✅ S4✅，待进入 S5

## 就绪度

- 产品定义：是 ✅（v2.0 Agent Quant 架构）
- 调研状态：是 ✅（含 Agent Quant / Harness / LLM 调研）
- 开发计划就绪：是 ✅（v2.0，S1-S12 三阶段）
- 切片开发：S1✅ S2✅ S3✅ S4✅
- 验证状态：S4 聚合测试 19/19 passed；非 slow 回归 77 passed, 5 deselected

## 已确认决策

- ✅ 回测引擎自建（Polars 向量化）
- ✅ 表达式引擎自建（DSL→AST→Polars，20 运算符）
- ✅ Gateway 模式（vnpy 风格）
- ✅ 数据源：Baostock + 腾讯 HTTP API
- ✅ Agent Quant 架构（多 Agent + 记忆 + 反思）
- ✅ LLM：用户自备 API Key（DeepSeek/Qwen/Claude），LiteLLM 统一调用
- ✅ 滑点模型：百分比滑点（默认 0.1%）
- ✅ 撮合模式：收盘价撮合（默认）

## 待确认

- AKShare 情绪专用接口已完成能力覆盖验证；S8 应按 provider fallback 链实现
- DeepSeek v4-flash 还是 v4-pro 做主力模型
- 记忆文件是否纳入 git 管理

## 恢复指令

读取 AGENTS.md、agent-foundry/WorkingContext.md、agent-foundry/DevPlan.md 和本文件，然后继续 S5 开发。
