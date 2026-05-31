---
name: finish-gate
description: 当准备结束会话、提交、推送、合并、发布或交付结果时使用。
---

# finish-gate

## 触发条件

- 本轮任务准备结束。
- 准备提交、推送、合并或发布。
- 准备把结果交给用户验收。

## 完成检查

- 已运行 verification-before-completion，且有新鲜验证证据。
- WorkingContext.md 已更新。
- 开发状态变化时 Progress.md 已更新。
- 调研变化时 Research.md 已更新，并链接独立调研文档。
- 有阶段经验时 Reflection.md 已更新。
- 有长期规则或重复反馈时 Memory.md 或 Feedback.md 已更新。
- Status.md 反映当前阶段和恢复指令。

## git 状态

必须检查 git 状态并说明：

- 哪些文件被修改。
- 哪些文件被忽略。
- 是否有不应提交的本地文件。
- 是否需要 commit、push、PR、保留分支或清理 worktree。

## 下一步动作

结束前必须给出下一步，不能只说完成。下一步可以是用户评审、继续某个切片、补调研、提交推送或开启下一阶段。

## 输出要求

返回验证证据、文档维护结果、git 状态、未解决风险和下一步动作。
