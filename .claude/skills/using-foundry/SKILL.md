---
name: using-foundry
description: 当需要启动、恢复或协调 Agent Foundry 项目闭环时使用。
---

# using-foundry

## 触发条件

- 新会话开始，需要读取当前项目状态并继续推进。
- 用户给出想法、产品变更、实现请求、bug 修复、审查请求或上线动作。
- 不确定当前应进入产品定义、调研、计划、开发、验证、复盘还是完成门禁。

## 启动恢复

1. 读取 AGENTS.md。
2. 读取 agent-foundry/WorkingContext.md 和 agent-foundry/Status.md。
3. 如果当前工作涉及开发切片，读取 agent-foundry/Progress.md。
4. 只按 WorkingContext.md 的指引继续读取当前阶段需要的文档，避免无意义扩大上下文。
5. 明确本轮要更新哪些运行时文档。

## 阶段识别

| 信号 | 下一步 |
|---|---|
| 想法、目标、用户、边界不清 | product-definition |
| 需要外部产品、技术、架构参考 | research-check |
| 产品定义已有但不能开发 | writing-dev-plan |
| 计划已有且切片明确 | executing-dev-plan |
| 需要并行或监督 | parallel-dispatch 或 subagent-development |
| 测试、构建、线上行为失败 | systematic-debugging |
| 准备声明完成 | verification-before-completion 和 finish-gate |

## 硬性门禁

- 每次实质性工作结束前，至少更新 WorkingContext.md。
- 阶段、切片、阻塞或验证状态变化时，同步更新 Status.md 和 Progress.md。
- 产生调研结论时，必须写入 agent-foundry/Research.md，并在需要时生成独立调研文档。
- 产生可复用经验时，写入 Reflection.md；能长期复用的规则沉淀到 Memory.md 或 Feedback.md。

## 输出要求

返回当前阶段、读取过的关键文档、执行的工作流、已更新文档、未解决风险和下一步动作。
