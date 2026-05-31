# Agent Foundry 工作协议

## 启动必读

1. 读取本文件。
2. 读取 `agent-foundry/WorkingContext.md`。
3. 读取 `agent-foundry/Status.md`。
4. 如果当前工作是开发切片，读取 `agent-foundry/Progress.md`。
5. 只读取 WorkingContext 中列出的当前阶段相关文件。

## 方法选择

行动前先选择对应的 Agent Foundry 工作流：

- 想法或产品要求不清楚：先澄清、调研，再写产品定义。
- 实现请求：先确认计划，再开发；除纯文档或配置变更外，默认测试先行。
- bug、构建失败或验证失败：先调查根因，再提出修复。
- 准备声明完成：先运行新的验证命令并记录证据。

如果当前工具环境安装了 Superpowers 插件，可以借用 brainstorming、writing plans、TDD、systematic debugging、verification 等纪律。但 Agent Foundry 仍必须维护自己的运行时文件，不能依赖 Superpowers 已安装。

## 完整闭环

默认按这个顺序推进：

```text
想法 -> 调研 -> 产品定义 -> 产品审查 -> 开发计划 -> 计划审查 -> 切片开发 -> 开发审查 -> 验证 -> 发布 -> 复盘与记忆
```

## 必须维护

每次完成实质性工作后，必须更新上下文和相关产物。最低要求是更新 `WorkingContext.md`。如果开发进度发生变化，还要更新 `Progress.md`。

## 子代理协议

Codex target 把子代理角色作为协议写在本文件中。主 agent 扮演 orchestrator，并在需要时显式执行 research-scout、product-reviewer、plan-reviewer、dev-reviewer、release-reviewer、debugger 或 memory-curator 的职责。

开发工作采用两阶段审查：先根据当前计划和验收标准检查规格一致性，再审查实现质量。规格审查未通过前，不进入质量审查。

## 完成门禁

停止前检查验证证据、WorkingContext、Progress、Research、Reflection、Memory、Feedback、Decisions、git 状态和下一步动作。
