---
name: subagent-development
description: 当实现计划包含可分派任务或需要监督型审查时使用。
---

# subagent-development

## 触发条件

- 当前切片可拆成多个相对独立任务。
- 需要研究、实现、审查、调试或记忆沉淀由不同角色监督。
- 用户担心产品设计或开发质量失控。

## 调度原则

- 主 agent 永远是 orchestrator，负责上下文、任务边界、验收和最终落盘。
- 子 agent 只处理明确输入和输出，不接管项目状态。
- 任务之间共享文件或强依赖时，串行执行；互不依赖时可并行。
- 子 agent 输出必须被主 agent 复核后才能进入项目文档或代码。

## 两阶段审查

实现类任务必须执行两阶段审查：

1. 规格一致性：对照 Product.md、DevPlan.md、验收故事和用户要求，确认做的是正确的东西。
2. 实现质量：检查代码结构、测试、错误处理、边界条件、可维护性和安全风险。

规格一致性未通过前，不进入实现质量审查。

## 子代理产物

每个子 agent 结果必须包含：

- 任务范围。
- 结论。
- 证据。
- 发现的问题。
- 建议动作。
- 需要写入 Memory.md、Feedback.md 或 Reflection.md 的候选内容。

## 输出要求

更新 WorkingContext.md；开发进度变化时更新 Progress.md；有监督结论时更新对应 Review 文档或 Reflection.md。
