---
name: requesting-review
description: 当完成产品定义、开发计划、实现切片或发布准备并需要审查时使用。
---

# requesting-review

## 触发条件

- Product.md、DevPlan.md 或实现切片已完成到可审查状态。
- 准备进入下一阶段前需要监督。
- 用户要求检查产品设计、计划或代码质量。

## 审查类型

| 产物 | 审查角色 | 重点 |
|---|---|---|
| Product.md | product-reviewer | 清晰度、边界、MVP、验收故事 |
| DevPlan.md | plan-reviewer | 颗粒度、切片、验证命令、风险 |
| 代码实现 | dev-reviewer | 规格一致性、实现质量、测试 |
| 发布准备 | release-reviewer | 验证证据、git 状态、回滚、文档 |

## 请求格式

审查请求必须包含：

- 当前阶段。
- 审查目标。
- 相关文件。
- 验收标准。
- 已运行验证。
- 已知风险。

## 输出要求

把审查请求和审查结论写入对应 Review 文档或 WorkingContext.md；返回阻塞问题、建议问题和可接受风险。
