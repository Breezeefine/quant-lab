---
name: executing-dev-plan
description: 当已有开发计划并准备执行一个明确切片时使用。
---

# executing-dev-plan

## 触发条件

- DevPlan.md 已存在可执行切片。
- 用户要求实现、修复或继续开发。
- Progress.md 指向当前切片或需要恢复中断的切片。

## 切片执行

1. 读取 DevPlan.md 和 Progress.md，确认当前切片目标。
2. 检查切片是否需要调研；需要时先执行 research-check。
3. 选择方法：普通实现、TDD、debugging、subagent-development 或 parallel-dispatch。
4. 修改前明确要改哪些文件和验证命令。
5. 小步实现，每完成可验证部分就记录 Progress.md。

## 开发纪律

- 除纯文档、纯配置或明确探索性任务外，默认使用 tdd-development。
- 不把计划外的大重构混入切片。
- 遇到失败先切到 systematic-debugging，不直接猜修。
- 实现完成后进入 requesting-review 或 dev-reviewer 审查。

## 进度记录

Progress.md 必须记录：

- 当前切片状态。
- 已改文件。
- 已运行验证。
- 阻塞和下一步。
- 新会话恢复所需的最小上下文。

## 输出要求

返回切片状态、代码变更、测试结果、Progress.md 更新点、风险和下一步。
