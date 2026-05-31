# 开发计划

版本：v2.0
日期：2026-05-31
状态：Agent Quant 架构重设计
基于：Product.md v2.0（Agent Quant）

---

## 架构总览

```
Phase 1: 基础设施（S1-S7）   ← 已完成 S1-S2，回测引擎 + 可视化
Phase 2: 情绪数据（S8-S9）   ← 新增，退学炒股数据基础
Phase 3: Agent 系统（S10-S12）← 新增，多 Agent 协作 + 记忆 + 反思
```

---

## Phase 1：基础设施（S1-S7）

### S1 数据就绪 ✅
- 状态：已完成
- 内容：Baostock Gateway + Parquet 存储
- 验证：10/10 测试通过

### S2 因子计算 ✅
- 状态：已完成
- 内容：DSL 解析器 + Polars 编译器 + 20 运算符
- 验证：47/47 测试通过

### S3 第一次回测
- 状态：待开发
- 内容：引擎核心循环 + 撮合引擎 + 买入持有策略
- 代码量：~600 行
- 验证：`uv run pytest tests/test_engine/ -v`

### S4 真实策略
- 状态：待开发
- 内容：双均线策略 + 限价单撮合 + 手续费
- 代码量：~500 行
- 验证：双均线回测产生交易记录

### S5 A 股规则
- 状态：待开发
- 内容：T+1 / 涨跌停 / 手续费 / 最小单位
- 代码量：~500 行
- 验证：违规订单被正确拒绝

### S6 模拟实盘
- 状态：待开发
- 内容：统一引擎 + SimBroker + 腾讯实时行情
- 代码量：~500 行
- 验证：同一策略代码在回测/实盘模式下都能运行

### S7 可视化
- 状态：待开发
- 内容：Streamlit 仪表盘（5 页面）
- 代码量：~500 行
- 验证：浏览器完成"选股→回测→看结果"闭环

---

## Phase 2：情绪数据（S8-S9）

### S8 情绪数据采集
- 状态：待开发
- 内容：涨停池/炸板池/跌停池/龙虎榜/板块资金流/北向资金
- 代码量：~500 行
- 依赖：S1（数据层基础设施）

**涉及文件**：
```
新增：
├── src/quant_lab/sentiment/__init__.py
├── src/quant_lab/sentiment/zt_gateway.py      # 涨停池/炸板池/跌停池
├── src/quant_lab/sentiment/lhb_gateway.py     # 龙虎榜
├── src/quant_lab/sentiment/sector_gateway.py  # 板块资金流
├── src/quant_lab/sentiment/north_gateway.py   # 北向资金
├── src/quant_lab/sentiment/storage.py         # 情绪数据 Parquet 存储
└── tests/test_sentiment/
    ├── test_zt_gateway.py
    └── test_lhb_gateway.py
```

**数据源优先级**：
1. AKShare 情绪专用接口（涨停池等可能绕过 TLS 反爬）
2. Tushare Pro（需积分，作为备选）
3. 腾讯 HTTP API（实时行情）

**验收**：
```
Given 运行情绪数据采集脚本
When  采集 2024-01-02 的数据
Then  Parquet 文件包含涨停池、炸板池、龙虎榜
And   字段完整（代码、名称、连板数、封板时间、炸板次数等）
```

### S9 情绪指标引擎
- 状态：待开发
- 内容：连板高度/炸板率/首板溢价率/情绪温度/龙头评分
- 代码量：~400 行
- 依赖：S8

**涉及文件**：
```
新增：
├── src/quant_lab/sentiment/indicators.py      # 情绪指标计算
├── src/quant_lab/sentiment/leader_scorer.py   # 龙头评分模型
├── src/quant_lab/sentiment/regime.py          # 市场状态机
└── tests/test_sentiment/
    ├── test_indicators.py
    └── test_regime.py
```

**核心指标**：
```python
# 情绪温度（0-100）
temperature = (
    0.20 * rank(涨停家数)
    + 0.15 * rank(1 / 跌停家数)
    + 0.20 * rank(首板溢价率)
    + 0.15 * rank(连板高度)
    + 0.15 * rank(1 - 炸板率)
    + 0.15 * rank(涨跌比)
)

# 龙头评分（0-1）
leader_score = (
    0.25 * 连板得分
    + 0.20 * 时间得分      # 首封时间越早越好
    + 0.20 * 封单得分      # 封单占比越高越好
    + 0.15 * (1 - 炸板次数/4)
    + 0.10 * 成交排名得分
    + 0.10 * 板块助攻得分
)

# 市场状态机
冰点(0-20) → 修复(20-40) → 发酵(40-60) → 高潮(60-80) → 退潮(80→下降)
```

**验收**：
```
Given 涨停池/炸板池数据
When  计算情绪指标
Then  连板高度 = MAX(所有连板数)
And   炸板率 = 炸板数 / (涨停数 + 炸板数)
And   情绪温度在 0-100 之间
And   市场状态机正确识别冰点/修复/发酵/高潮/退潮
```

---

## Phase 3：Agent 系统（S10-S12）

### S10 Agent 框架
- 状态：待开发
- 内容：多 Agent 编排 + 记忆系统 + LLM 集成
- 代码量：~800 行
- 依赖：S8, S9

**涉及文件**：
```
新增：
├── src/quant_lab/agent/__init__.py
├── src/quant_lab/agent/llm_router.py         # LiteLLM 多模型路由
├── src/quant_lab/agent/memory.py             # 记忆系统（读写 trade_history 等）
├── src/quant_lab/agent/prompts.py            # Prompt 模板
├── src/quant_lab/agent/scanner.py            # 扫描 Agent 逻辑
├── src/quant_lab/agent/sentiment_analyzer.py # 情绪分析 Agent
├── src/quant_lab/agent/leader_finder.py      # 龙头识别 Agent
├── src/quant_lab/agent/reporter.py           # 报告生成 Agent
├── src/quant_lab/agent/reflect.py            # 反思 Agent
└── .claude/agents/                           # Claude Code 子 Agent 定义
    ├── scanner-agent.md
    ├── sentiment-agent.md
    ├── leader-agent.md
    └── report-agent.md
```

**LLM 配置**：
```python
# src/quant_lab/config.py 新增
class LLMConfig(BaseModel):
    deepseek_api_key: str | None = None      # env: DEEPSEEK_API_KEY
    dashscope_api_key: str | None = None     # env: DASHSCOPE_API_KEY
    anthropic_api_key: str | None = None     # env: ANTHROPIC_API_KEY
    provider_chain: list[str] = ["deepseek", "qwen", "claude"]
    max_daily_cost_usd: float = 5.0
```

**验收**：
```
Given 配置了 DEEPSEEK_API_KEY
When  运行 Agent 扫描
Then  scanner-agent 调用 LLM 筛选候选股
And   结果保存到 memory/trade_history.jsonl
And   LLM 调用有 fallback（DeepSeek 失败自动切 Qwen）
```

### S11 退学炒股策略
- 状态：待开发
- 内容：龙头识别 + 情绪周期驱动 + 打板策略
- 代码量：~600 行
- 依赖：S9, S10

**涉及文件**：
```
新增：
├── src/quant_lab/strategy/退学炒股/
│   ├── __init__.py
│   ├── leader_strategy.py    # 龙头打板策略
│   ├── sentiment_timing.py   # 情绪择时策略
│   └── rules.py              # 退学炒股交易规则
└── tests/test_strategy/
    └── test_leader_strategy.py
```

**退学炒股核心规则**：
```python
# 冰点期：空仓观望，等待信号
# 修复期：轻仓试错首板龙头
# 发酵期：加仓确认龙头（2-3 板）
# 高潮期：逢高减仓，不再追高
# 退潮期：清仓，等待冰点

# 打板规则：
# - 只打龙头，不打跟风
# - 封板时间 < 10:30 才考虑
# - 炸板次数 > 2 不考虑
# - 板块内有 3+ 涨停才考虑板块效应
```

**验收**：
```
Given 情绪指标 + 龙头评分
When  运行退学炒股策略回测
Then  策略在冰点期空仓
And   在发酵期持有龙头股
And   在高潮期减仓
And   回测结果包含完整交易记录
```

### S12 报告与进化
- 状态：待开发
- 内容：每日推荐报告 + 可视化 + 反思循环 + 策略版本管理
- 代码量：~500 行
- 依赖：S10, S11

**涉及文件**：
```
新增/修改：
├── src/quant_lab/agent/daily_report.py       # 每日报告生成
├── src/quant_lab/agent/reflection.py         # 反思循环
├── app/pages/6_情绪面板.py                    # 情绪可视化
├── app/pages/7_Agent报告.py                   # Agent 报告展示
├── memory/                                    # 记忆目录
│   ├── MEMORY.md
│   ├── trade_history.jsonl
│   ├── lessons_learned.md
│   ├── strategy_current.md
│   └── strategy_changelog.md
└── scripts/daily_scan.py                     # 每日扫描脚本
```

**验收**：
```
Given Agent 完成分析
When  生成每日报告
Then  报告包含 Top 10 推荐股
And   每只股有：代码、题材、地位、阶段、止损、信心度
And   报告可读性强，格式清晰

Given 一笔交易完成（T+2）
When  reflect-agent 分析
Then  生成反思笔记
And   写入 lessons_learned.md
```

---

## 切片总览

| 切片 | 名称 | Phase | 状态 | 代码量 | 依赖 |
|------|------|-------|------|--------|------|
| S1 | 数据就绪 | 1 | ✅ | ~400 行 | — |
| S2 | 因子计算 | 1 | ✅ | ~800 行 | S1 |
| S3 | 第一次回测 | 1 | 待开发 | ~600 行 | S1 |
| S4 | 真实策略 | 1 | 待开发 | ~500 行 | S2, S3 |
| S5 | A 股规则 | 1 | 待开发 | ~500 行 | S4 |
| S6 | 模拟实盘 | 1 | 待开发 | ~500 行 | S5 |
| S7 | 可视化 | 1 | 待开发 | ~500 行 | S6 |
| S8 | 情绪数据 | 2 | 待开发 | ~500 行 | S1 |
| S9 | 情绪指标 | 2 | 待开发 | ~400 行 | S8 |
| S10 | Agent 框架 | 3 | 待开发 | ~800 行 | S8, S9 |
| S11 | 退学炒股策略 | 3 | 待开发 | ~600 行 | S9, S10 |
| S12 | 报告与进化 | 3 | 待开发 | ~500 行 | S10, S11 |

**总代码量**：~6100 行

---

## 执行顺序

```
Phase 1:  S1 ✅ → S2 ✅ → S3 → S4 → S5 → S6 → S7
                                              ↓
Phase 2:                               S8 → S9
                                              ↓
Phase 3:                              S10 → S11 → S12
```

**可并行**：
- S3 和 S8 无依赖，可并行开发
- S7 和 S9 无依赖，可并行开发

---

## 验证命令汇总

```bash
# Phase 1 测试
uv run pytest tests/test_data/ -v          # S1
uv run pytest tests/test_expression/ -v    # S2
uv run pytest tests/test_engine/ -v        # S3-S6
uv run pytest tests/test_strategy/ -v      # S4
uv run pytest tests/test_app/ -v           # S7

# Phase 2 测试
uv run pytest tests/test_sentiment/ -v     # S8-S9

# Phase 3 测试
uv run pytest tests/test_agent/ -v         # S10-S12

# 完整闭环
uv run python scripts/fetch_data.py --symbol 600000 --start 2024-01-01 --end 2024-12-31
uv run python scripts/run_backtest.py --strategy dual_ma --symbol 600000
uv run python scripts/daily_scan.py --date 2024-12-31
uv run streamlit run app/Home.py
```

---

## 风险总览

| 风险 | 影响 | 规避措施 |
|------|------|----------|
| AKShare 情绪接口被封 | S8 数据采集失败 | 多源备选（AKShare → Tushare → 爬虫） |
| LLM API 不稳定 | Agent 无法运行 | LiteLLM fallback + 本地缓存 |
| LLM 成本超预期 | 月费过高 | DeepSeek 为主（$2/月），设置日限额 |
| Agent 推荐质量差 | 人类不信任 | 反思循环持续改进，人类始终有否决权 |
| 记忆文件过大 | 上下文超限 | 定期归档，只加载最近 N 条 |
| 策略回测过拟合 | 实盘表现差 | 用样本外数据验证，人类最终判断 |
