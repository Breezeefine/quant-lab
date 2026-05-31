---
name: writing-foundry-skills
description: 当需要新增、修改或审查 Agent Foundry workflow skill 时使用。
---

# writing-foundry-skills

## 触发条件

- 新增 Foundry workflow skill。
- 修改 .claude/skills 生成模板。
- 某个 skill 触发不准、内容太泛或无法约束 agent 行为。

## 编写原则

- description 只写触发条件，不压缩正文流程。
- 正文必须有明确触发条件、输入、步骤、门禁和输出要求。
- 每个 skill 只负责一个 workflow，不复制通用模板。
- 能自动化检查的规则优先写测试或 validate，不只写文档。

## 测试要求

- 先写能失败的生成器测试或内容检查。
- 再修改模板。
- 运行生成器测试、全量测试和 validate。
- 当前项目已生成的 .claude/skills 也要同步更新。

## 质量检查

- skill 名称只使用小写字母、数字和连字符。
- 中文输出默认完整，不混入英文标题模板。
- 不写一次性叙事；只写可复用流程和判断。

## 输出要求

返回新增或修改的 skill、测试证据、生成文件、上下文更新和后续改进点。
