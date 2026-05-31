# 个人量化操作系统 — 调研报告

调研日期：2026-05-31
调研人：research-scout（并行 4 路）

---

## 一、A 股数据源

### 推荐：Baostock（历史数据）+ 新浪/腾讯（实时行情）

**2026-05-31 更新**：实测发现东方财富 `push2his.eastmoney.com` API 存在 TLS 层反爬机制，Python requests/curl 均被服务器主动断开连接。AKShare 和 efinance 底层均依赖此 API，因此不可用。

| 数据源 | 日线 | 5min线 | 1min线 | Tick | 实时行情 | 数据源方 | 状态 |
|--------|------|--------|--------|------|----------|----------|------|
| **Baostock** | ✅ | ✅ | ❌ | ❌ | ❌ | 自有服务器 | ✅ 已验证可用 |
| **新浪财经** | — | — | — | — | ✅ | 新浪 | ✅ 已验证可用 |
| **腾讯财经** | — | — | — | — | ✅ | 腾讯 | ✅ 已验证可用 |
| AKShare | ✅ | ✅ | ✅ | 有限 | ✅ | 东方财富 | ❌ 反爬被封 |
| efinance | ✅ | ✅ | ✅ | ✅ | ✅ | 东方财富 | ❌ 反爬被封 |
| TuShare Pro | ✅ | ✅ | ❌ | ❌ | ✅ | 自有 | 积分制 |

**决策**：
- **历史数据 + 分钟线回测** → Baostock（日线 + 5min，免费无注册，自有服务器直连）
- **实时行情（S6 模拟实盘）** → 新浪或腾讯 HTTP API（简单 GET 请求，无需注册）
- **1 分钟线** → 免费源均无可靠支持，MVP 先用 5min

### 风险

- Baostock 1 分钟线数据不可用，回测精度限制在 5 分钟级别
- 新浪/腾讯实时行情有 3-15 秒延迟（免费接口通病）
- 如需 Tick 级数据，需考虑券商 QMT（xtquant）方案

---

## 二、回测引擎

### 方案对比

| 方案 | Stars | A股支持 | 学习曲线 | 维护状态 | 实盘对接 | AI友好度 |
|------|-------|---------|----------|----------|----------|----------|
| backtrader | 21.8k | 需自行对接 | 中等 | 停滞(2021) | IB/Oanda | 中 |
| vnpy | 41.2k | 原生支持 | 较陡 | 活跃(4.0) | 多券商 | 高 |
| qlib | 43.8k | 原生支持 | 较陡 | 活跃 | 无原生 | 极高 |
| rqalpha | 6.4k | 原生支持 | 平缓 | 活跃 | 需商业版 | 中 |
| 自建 | - | 完全可控 | 最低 | - | 自定义 | 最高 |

### 推荐：MVP 自建轻量回测引擎

**理由**：
1. 核心逻辑不超过 500 行，AI 完全可以生成和维护
2. 每一行代码都在项目控制之下，无黑箱
3. 精确适配 A 股规则（涨跌停、T+1、手续费结构）
4. 基于 Polars 向量化计算，性能优异
5. 零学习成本，不需理解第三方框架内部机制

**架构**：
```
策略层（用户编写）→ 信号生成（Polars 表达式）
                        ↓
                   回测引擎（向量化计算收益、滑点、手续费）
                        ↓
                   绩效分析（夏普、最大回撤等指标）
```

**后续进阶**：
- 需要 AI 能力时参考 qlib 的表达式引擎
- 需要实盘时参考 vnpy 的 Gateway 模式

---

## 三、技术架构

### 推荐栈

| 层次 | 选择 | 理由 |
|------|------|------|
| Python 版本 | 3.12 | 生态兼容性最佳，错误消息改进利于 AI |
| 包管理 | uv | Rust 实现极快，内置 Python 管理，workspace 支持 |
| 数据处理 | Polars（主） | 比 Pandas 快 10-100x，API 声明式，AI 生成更准确 |
| 查询引擎 | DuckDB | 嵌入式，直接查询 Parquet，零运维 |
| 文件存储 | Parquet | 列式存储，按股票代码/年份分区 |
| 元数据 | SQLite | 配置、交易记录、回测记录 |
| 可视化 | Streamlit | 纯 Python 写 UI，零前端知识，量化场景匹配 |
| 图表 | Plotly | 交互式 K 线图、收益曲线 |
| 配置校验 | Pydantic | 声明式 schema，AI 有明确约束参考 |
| 日志 | loguru | 简洁优雅的 Python 日志 |
| 测试 | pytest | Python 标准 |

### 存储架构

```
data/
├── raw/                    # 原始数据（Parquet）
│   ├── cn_stock/
│   │   ├── daily/
│   │   │   └── SH600000/   # 按股票代码分区
│   │   └── minute/
│   └── index/
├── processed/              # 清洗后数据（Parquet）
├── features/               # 特征数据（Parquet）
└── metadata.db             # SQLite 元数据库
```

### 部署策略

| 阶段 | 方式 |
|------|------|
| MVP（回测） | 本地 `uv run` |
| 分享展示 | Docker Compose |
| 实盘（未来） | Docker + 云 VPS |

---

## 四、开源项目参考

### 架构模式借鉴

| 模式 | 来源 | 应用场景 |
|------|------|----------|
| Gateway 适配器 | vnpy | 交易所/数据源统一接口，换源只改一个文件 |
| 表达式引擎（DSL） | qlib | 用字符串定义因子，向量化求值 |
| Point-in-Time | qlib | 防前视偏差，回测硬性要求 |
| Algorithm Framework | Lean | Alpha→Risk→Portfolio→Execution 流水线 |
| Mod 钩子系统 | rqalpha | 功能模块可插拔、可替换 |
| 确定性事件驱动 | NautilusTrader | 回测与实盘结果完全一致 |
| 统一引擎 | Lean/Nautilus | 回测与实盘共用同一引擎 |

### 关键发现

1. "统一引擎"是行业共识 — 回测与实盘共用同一代码路径
2. Python 仍是主流，但性能关键路径开始向 Rust/C++ 迁移
3. AI 量化（qlib RD-Agent）是未来趋势

---

## 五、综合建议

### MVP 技术方案

```
uv + Python 3.12 + Polars/DuckDB + Parquet + Streamlit + 自建回测引擎
```

### 项目结构

```
quant-lab/
├── pyproject.toml
├── CLAUDE.md                   # AI 开发指南
├── src/quant_lab/
│   ├── config.py               # Pydantic 配置
│   ├── data/                   # 数据层
│   │   ├── baostock_gateway.py # Baostock 数据源
│   │   ├── sina_gateway.py     # 新浪实时行情
│   │   ├── storage.py          # Parquet/DuckDB 读写
│   │   └── schemas.py          # 数据模型
│   ├── backtest/               # 回测引擎
│   │   ├── engine.py           # 核心回测循环
│   │   ├── portfolio.py        # 组合管理
│   │   └── metrics.py          # 绩效指标
│   ├── strategy/               # 策略层
│   │   ├── base.py             # 策略基类
│   │   └── examples/           # 示例策略
│   └── utils/                  # 工具
├── app/                        # Streamlit 前端
├── tests/                      # 测试
├── scripts/                    # 工具脚本
└── data/                       # 数据存储（.gitignore）
```

### MVP 路径（7 步）

| 步骤 | 内容 | 验证标准 |
|------|------|----------|
| 1 | 项目脚手架 | `uv run python -c "import quant_lab"` 成功 |
| 2 | 数据采集 | 能下载并存储至少一只股票的日线数据 |
| 3 | 数据加载 | 能读取并展示数据统计摘要 |
| 4 | 回测引擎 | 给定买入持有信号，计算正确收益 |
| 5 | 策略示例 | 双均线策略产生信号→引擎回测→输出指标 |
| 6 | Streamlit | 浏览器中展示回测结果图表 |
| 7 | 绩效指标 | 夏普、最大回撤等指标计算正确 |

### 关键依赖

```
polars>=1.0, duckdb>=1.0, pyarrow>=15.0, akshare>=1.12,
streamlit>=1.30, plotly>=5.18, pydantic>=2.5, loguru>=0.7,
exchange-calendars>=4.5
```

---

## 六、待确认决策

1. **回测引擎**：自建 vs 采用 rqalpha？（报告推荐自建）
2. **数据存储**：Parquet+DuckDB+SQLite 是否满足需求？
3. **前端**：Streamlit 是否接受，还是需要更灵活的方案？

---

## 七、聚焦深潜调研（第二轮）

### 7.1 qlib 表达式引擎 — 移植到 Polars

**核心发现**：qlib 没有传统 AST 解析器，而是利用 `parse_field()` 正则替换 + Python `eval()` + 运算符重载实现极简 DSL→对象树映射。

**DSL 示例**：
```
"Mean($close, 20) / $close - 1"
→ eval → Operators.Mean(Feature("close"), 20) / Feature("close") - 1
→ 自动构建运算符对象树
```

**移植到 Polars 需自研的部分**：

| 模块 | 工作量 | 说明 |
|------|--------|------|
| DSL 解析器 | 200-300 行 | 词法分析→语法分析→AST |
| AST→Polars 编译器 | ~200 行 | AST 转 `pl.Expr` 链式调用 |
| 特殊运算符 UDF | 6-8 个 | Slope/Rsquare/Resi/WMA/Rank 等窗口函数 |
| 缓存系统 | 300-500 行 | 内存 DataFrame 缓存 + Parquet 磁盘缓存 |
| **总计** | **~1000-1500 行** | |

**可直接映射到 Polars 的运算符**（约 20+ 个）：
- `Ref(x,N)` → `col(x).shift(N)`
- `Mean(x,N)` → `col(x).rolling_mean(N)`
- `Std/Sum/Var/Max/Min` → 对应 `rolling_*` 方法
- `Delta(x,N)` → `col(x) - col(x).shift(N)`
- `EMA(x,N)` → `col(x).ewm_mean(span=N)`
- `If(cond,x,y)` → `when(cond).then(x).otherwise(y)`

**关键设计决策**：
- 数据模型：`(instrument, datetime)` 双索引 DataFrame，按 instrument 分组后应用滚动窗口
- 编译方式：两遍编译 — DSL→AST→Polars 表达式链
- 并行计算：利用 Polars 内置 Rust rayon 并行，无需手动并行
- 扩展性：`register_operator(name, polars_func)` 注册机制

### 7.2 vnpy Gateway 模式 — 数据源和交易所接入层

**核心架构**：事件驱动 + 抽象工厂模式

**最小可用 Gateway 接口**：
```python
class BaseGateway(ABC):
    connect(config) → bool          # 连接
    disconnect() → None             # 断开
    subscribe(symbols) → None       # 订阅行情
    send_order(symbol, direction, price, volume) → str  # 下单
    cancel_order(order_id) → bool   # 撤单
    get_account() → dict            # 查询账户
    get_positions() → List[dict]    # 查询持仓
    on_tick(callback)               # 注册行情回调
    on_order(callback)              # 注册订单回调
    on_trade(callback)              # 注册成交回调
```

**核心数据模型**（dataclass）：
- `TickData` — Tick 行情（symbol, exchange, datetime, last_price, bid/ask 等）
- `BarData` — K 线（symbol, exchange, datetime, OHLCV）
- `OrderData` — 委托（orderid, symbol, direction, price, volume, status）
- `TradeData` — 成交（tradeid, orderid, price, volume）
- `PositionData` — 持仓（symbol, volume, frozen, price, pnl）
- `AccountData` — 账户（balance, frozen, available）

**EventEngine 事件引擎**：
- Queue + Thread 实现发布-订阅
- `register(event_type, handler)` 注册处理函数
- `put(event)` 推送事件
- 支持定时器事件（每秒触发）

**我们的 Gateway 实现计划**：
- `BaostockGateway` — 历史数据网关（Baostock 直连，日线+分钟线）
- `SinaQuoteGateway` — 实时行情网关（新浪财经 HTTP API）
- `SimBrokerGateway` — 模拟交易网关（即时撮合，A股规则）
- `GatewayManager` — 统一管理多个 Gateway

### 7.3 模拟实盘系统 — 统一引擎设计

**核心发现**：回测和模拟实盘应共用同一套核心逻辑，仅替换数据源和时间驱动方式。

**统一引擎架构**：
```
DataFeed（数据源）→ Strategy（策略）→ Order（订单）
→ RiskCheck（风控）→ MatchingEngine（撮合）
→ PositionManager（持仓）→ Account（账户）→ Performance（绩效）
```

**A 股规则引擎（必须精确实现）**：
- T+1：买入当日冻结，次日转可卖
- 涨跌停：主板±10%，创业板/科创板±20%，ST±5%
- 手续费：佣金万2.5（最低5元）+ 印花税千1（仅卖出）+ 过户费十万分之二
- 最小交易单位：主板 100 股，科创板 200 股

**撮合引擎**：
- 支持限价单/市价单
- Bar 级别撮合：开盘价/收盘价/VWAP 三种模式
- 滑点模拟：百分比滑点（买入上浮，卖出下浮）

**绩效归因指标**：
- 夏普比率、最大回撤、Sortino 比率、Calmar 比率
- 胜率、盈亏比、交易次数
- 时间加权收益率、资金加权收益率

**共用 vs 分离**：

| 共用组件 | 分离组件 |
|----------|----------|
| StrategyBase 策略基类 | DataFeed 实现（历史 vs 实时） |
| AStockRules A股规则 | 时间驱动（事件循环 vs 定时器） |
| PositionManager 持仓管理 | 订单执行（即时 vs 延迟） |
| PerformanceAnalyzer 绩效分析 | |
| CommissionCalculator 手续费 | |

---

## 八、更新后的 MVP 范围

基于深潜调研，MVP 范围扩展为：

| 模块 | 内容 | 代码量估计 |
|------|------|-----------|
| 数据层 | Baostock Gateway + Parquet 存储 + 新浪实时行情 | ~500 行 |
| 表达式引擎 | DSL 解析器 + Polars 编译器 + 基础运算符 | ~1000 行 |
| 回测引擎 | 向量化回测 + 撮合引擎 + A 股规则 | ~800 行 |
| 模拟实盘 | 统一引擎 + SimBroker Gateway | ~600 行 |
| 策略层 | 策略基类 + 双均线示例 | ~300 行 |
| 绩效分析 | 夏普/回撤/胜率等指标 | ~300 行 |
| 可视化 | Streamlit 仪表盘 | ~500 行 |
| **总计** | | **~4000 行** |

---

## 九、待确认决策（更新）

1. ~~回测引擎自建~~ → ✅ 已确认自建
2. ~~表达式引擎~~ → ✅ 已确认在 MVP 阶段完成（基于 Polars）
3. ~~Gateway 模式~~ → ✅ 已确认采用 vnpy 模式
4. **撮合模式**：默认收盘价撮合，是否需要支持开盘价/VWAP？
5. **滑点模型**：固定滑点 vs 百分比滑点？
6. **表达式引擎范围**：MVP 需要支持多少运算符？（建议先支持 20 个核心运算符）

---

## 十、Quant Agent 与"退学炒股"架构调研（2026-05-31）

### 10.1 调研背景

用户目标：量化实现"退学炒股"策略体系（打板、龙头战法、情绪周期）。
当前系统：规则型回测引擎，仅支持价格因子和日线数据。
调研目的：评估是否需要架构重设计，避免后续重构成本。

### 10.2 行业格局（2026）

| 框架 | Stars | 定位 | 核心架构 | A股支持 |
|------|-------|------|----------|---------|
| **FinRL-X/Trading** | 3.2k | AI 原生交易基础设施 | 权重中心 SART 流水线 | 需适配 |
| **FinGPT** | 20.3k | 金融 LLM | 4 层数据驱动流水线 | ✅ 有中文模型 |
| **FinRobot** | 7.1k | AI Agent 平台 | Perception-Brain-Action | 需适配 |
| **Qlib + RD-Agent** | 43.8k | LLM 驱动因子挖掘 | 自动量化工厂 | ✅ CSI300/500 |
| **TradingGPT** | — | 多 Agent 协作 | 分析师辩论共识 | 需适配 |

### 10.3 FinRL-X 核心架构：权重中心设计

**SART 流水线**：`w_t = R_t( T_t( A_t( S_t( X_{<=t} ) ) ) )`

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **S** Selection | 选股 | 全量数据 | 候选集 |
| **A** Allocation | 配置 | 候选集 | 基础权重向量 |
| **T** Timing | 择时 | 基础权重 | 择时调整权重 |
| **R** Risk | 风控 | 择时权重 | 最终权重向量 |

**核心接口**（可借鉴）：
```python
class BaseStrategy:
    def generate_weights(self, data, target_date=None) -> StrategyResult:
        """每个模块输出统一的权重向量，可随意替换"""
        raise NotImplementedError
```

**对我们系统的启示**：回测引擎的 `on_bar()` → Signal 接口已经类似，但缺少多维度信号输入。

### 10.4 "退学炒股"量化要素

#### 数据需求

| 数据类型 | 来源 | 频率 | 用途 |
|----------|------|------|------|
| 涨停池 | AKShare `stock_zt_pool_em` | 日 | 连板统计、龙头识别 |
| 炸板池 | AKShare `stock_zt_pool_zbgc_em` | 日 | 炸板率计算 |
| 跌停池 | AKShare `stock_zt_pool_dtgc_em` | 日 | 情绪温度 |
| 龙虎榜 | AKShare `stock_lhb_detail_em` | 日 | 游资/机构动向 |
| 板块资金流 | AKShare `stock_sector_fund_flow_rank` | 日 | 板块轮动 |
| 北向资金 | AKShare `stock_hsgt_north_net_flow_in_em` | 日 | 外资情绪 |
| 热度排名 | AKShare `stock_hot_rank_em` | 日 | 散户情绪 |
| 实时行情 | 腾讯 `qt.gtimg.cn` | 秒 | 盘中监控 |
| 5min K线 | Baostock | 5min | 分时回测 |

**关键发现**：AKShare 的 eastmoney API 被 TLS 反爬，但涨停池等专用接口**可能仍可用**（不同于 `stock_zh_a_hist` 的通用接口）。需要实际测试验证。

#### 核心指标公式

```
连板高度 = MAX(所有股票的连板数)
炸板率 = 炸板数 / (涨停数 + 炸板数)
首板溢价率 = SUM(首板股次日开盘 - 首板涨停价) / SUM(首板涨停价)
涨跌比 = 上涨家数 / 下跌家数
赚钱效应 = (涨停家数 - 跌停家数) / (涨停家数 + 跌停家数)

情绪温度 = 0.20*标准化(涨停家数) + 0.15*标准化(1/跌停家数)
         + 0.20*标准化(首板溢价率) + 0.15*标准化(连板高度)
         + 0.15*标准化(1-炸板率) + 0.15*标准化(涨跌比)
```

#### 情绪周期状态机

```
冰点(0-20) → 修复(20-40) → 发酵(40-60) → 高潮(60-80) → 退潮(80→下降)
```

| 周期 | 涨停家数 | 连板高度 | 炸板率 | 操作 |
|------|---------|---------|--------|------|
| 冰点 | <10 | ≤2 | >50% | 空仓观望 |
| 修复 | 增加 | 2-3 | 下降 | 轻仓试错 |
| 发酵 | 30-60 | 3-5 | <30% | 加仓龙头 |
| 高潮 | >80 | ≥5 | <20% | 逢高减仓 |
| 退潮 | 下降 | 断板 | 飙升 | 清仓 |

#### 龙头股评分模型

```
龙头得分 = 0.25*连板得分 + 0.20*时间得分 + 0.20*封单得分
         + 0.15*(1-炸板次数/4) + 0.10*成交排名 + 0.10*板块助攻
```

### 10.5 LLM 集成建议

| 模式 | 用途 | 延迟 | 成本 | 优先级 |
|------|------|------|------|--------|
| **情绪分析** | FinGPT 对新闻/帖子打分 | 小时级 | 低 | 高 |
| **策略生成** | NL→代码（RD-Agent 模式） | 离线 | 中 | 中 |
| **风控审查** | LLM Review 风险评论 | 日级 | 低 | 低 |
| **市场研判** | LLM 判断情绪周期 | 日级 | 低 | 中 |

**核心原则**：LLM 是顾问，不是执行者。所有交易决策由规则引擎执行。

### 10.6 实时数据 API 评估

| API | 数据 | 稳定性 | 备注 |
|-----|------|--------|------|
| 腾讯 `qt.gtimg.cn` | L1 实时报价 | ⭐⭐⭐ | 需 Referer header，HTTP |
| 新浪 `hq.sinajs.cn` | L1 实时报价 | ⭐⭐ | 不稳定，Referer 验证 |
| AKShare 涨停池 | 涨停/炸板/跌停 | ⭐⭐⭐ | eastmoney 接口，需测试 |
| Baostock 5min | 5min K线 | ⭐⭐⭐⭐ | 自有服务器，最稳定 |
| Tushare Pro | 多种 | ⭐⭐⭐ | 需积分，部分付费 |
| QMT/PTrade | L2 Tick | ⭐⭐⭐⭐⭐ | 需券商账户 50万+ |

### 10.7 架构重设计方案

#### 方案 A：最小改动（推荐）

在现有架构上扩展，不改变核心接口：

```
现有 S1-S7 保持不变，新增：
S8: 情绪数据层（涨停池/炸板池/龙虎榜采集 + 存储）
S9: 情绪指标引擎（连板高度/炸板率/首板溢价/情绪温度）
S10: 市场状态机（冰点→修复→发酵→高潮→退潮）
S11: 打板策略（龙头评分 + 情绪周期驱动 + 回测验证）
S12: LLM 辅助（FinGPT 情绪分析 + 策略建议）
```

**改动量**：~2000 行新增代码，现有代码改动 <100 行
**优势**：风险最低，现有 S1-S7 进度不浪费
**劣势**：不是最优架构，后续如需重构仍有成本

#### 方案 B：FinRL-X 风格重设计

重新设计核心接口为权重中心架构：

```
DataFeed(统一) → Selection(选股) → Allocation(配置) → Timing(择时) → Risk(风控) → 执行
```

**改动量**：现有 S1-S2 保留，S3-S7 重写，新增 S8-S12
**优势**：架构最优，模块可替换，扩展性强
**劣势**：S3-S7 返工，开发周期延长

#### 推荐：方案 A

理由：
1. 用户是量化新手，MVP 阶段最重要的是**跑通闭环**，不是架构完美
2. 现有 S1-S7 的核心设计（Gateway 模式、表达式引擎、统一引擎）已经足够好
3. "退学炒股"的数据和指标可以作为**独立模块**加入，不影响现有架构
4. 后续如果真的需要 FinRL-X 级别的模块化，可以渐进重构

### 10.8 修订后的开发计划

| 切片 | 名称 | 状态 | 说明 |
|------|------|------|------|
| S1 | 数据就绪 | ✅ 完成 | |
| S2 | 因子计算 | ✅ 完成 | |
| S3 | 第一次回测 | 待开发 | 不变 |
| S4 | 真实策略 | 待开发 | 不变 |
| S5 | A 股规则 | 待开发 | 不变 |
| S6 | 模拟实盘 | 待开发 | 实时行情改用腾讯 API |
| S7 | 可视化 | 待开发 | 新增情绪面板 |
| **S8** | **情绪数据层** | **新增** | 涨停池/炸板池/龙虎榜采集存储 |
| **S9** | **情绪指标引擎** | **新增** | 连板高度/炸板率/情绪温度计算 |
| **S10** | **市场状态机** | **新增** | 五周期状态机 + 转换规则 |
| **S11** | **打板策略** | **新增** | 龙头评分 + 情绪驱动回测 |
| **S12** | **LLM 辅助** | **新增** | FinGPT 情绪分析（可选） |

**总代码量**：~4000 行（S1-S7）+ ~2000 行（S8-S11）= ~6000 行

---

## 十一、Harness 执行容器模式调研（2026-05-31）

### 11.1 什么是 Harness

"Harness"不是某个具体产品，而是软件工程术语——**执行容器/运行时包装器**。在量化交易中指：

> 把策略代码包裹起来，统一处理数据源、订单、风控、事件循环的框架层

行业中的 Harness 实现：

| 框架 | Stars | Harness 模式 | 核心特点 |
|------|-------|-------------|----------|
| **NautilusTrader** | 23.2k | 确定性事件驱动 | Rust 内核，回测=实盘零改动 |
| **QuantConnect/LEAN** | 20k | 算法框架 | 300+ 对冲基金使用 |
| **FinRL-X** | 3.2k | 权重中心 SART | 模块可替换 |
| **vnpy** | 41.2k | Gateway + 事件引擎 | A 股生态最成熟 |

### 11.2 核心价值：回测=实盘

```python
# NautilusTrader 模式：同一代码，不同引擎
class MyStrategy(Strategy):
    def on_bar(self, bar):
        if self.should_buy(bar):
            self.submit_order(...)

# 回测
engine = BacktestEngine()
engine.add_strategy(MyStrategy(...))
engine.run()

# 实盘 —— 同一个策略类，零改动
node = TradingNode()
node.add_strategy(MyStrategy(...))
node.run()
```

### 11.3 我们的 Harness 设计

我们的统一引擎（S3-S7）本质上就是一个轻量 Harness：

```
DataFeed → Strategy → Order → RiskCheck → Matching → Position → Account → Performance
```

**已实现**：Gateway 模式（数据源抽象）、策略基类（on_bar 接口）
**待实现**：撮合引擎（S3）、A 股规则（S5）、SimBroker（S6）

---

## 十二、LLM 多模型集成调研（2026-05-31）

### 12.1 提供商对比

| 提供商 | 模型 | 输入成本/1M tokens | 并发 | 中文金融 NLP | 特点 |
|--------|------|-------------------|------|-------------|------|
| **DeepSeek** | v4-flash | $0.14（缓存 $0.003） | 2500 rpm | ⭐⭐⭐⭐ | 幻方量化出品，量化基因 |
| **Qwen** | qwen-max | ~$0.28 | ~200 rpm | ⭐⭐⭐⭐⭐ | 阿里中文语料最强 |
| **Claude** | sonnet-4 | $3.0 | ~50 rpm | ⭐⭐⭐ | 复杂推理最强 |
| **GPT** | gpt-4o | $2.5 | ~500 rpm | ⭐⭐⭐ | 生态最广 |

### 12.2 月成本估算（1 万条新闻/月）

| 提供商 | 月成本 |
|--------|--------|
| DeepSeek | ~$2 |
| Qwen | ~$4 |
| Claude | ~$51 |
| GPT | ~$45 |

### 12.3 推荐方案：LiteLLM Router 统一接口

```python
# 用户配置 API Key 后，自动 fallback
DeepSeek（主力）→ Qwen（中文深度）→ Claude（复杂推理）→ GPT（兜底）
```

**核心原则**：LLM 是顾问，不是执行者。所有交易决策由规则引擎执行。

### 12.4 集成架构

```
src/quant_lab/
    llm/                        # LLM 模块
        __init__.py
        config.py               # 提供商配置（API Key、端点、限速）
        router.py               # LiteLLM Router 封装
        prompts.py              # A 股分析 Prompt 模板
        sentiment.py            # 情绪分析流水线
```

### 12.5 DeepSeek 特别说明

- `deepseek-chat` 和 `deepseek-reasoner` 将于 2026-07-24 下线
- 映射到 `deepseek-v4-flash` 的非思考/思考模式
- API 兼容 OpenAI 格式，base_url 改为 `https://api.deepseek.com`

### 12.6 Qwen 特别说明

- 平台：阿里云 DashScope（百炼）
- OpenAI 兼容模式 base_url：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- Qwen-Long 支持 1M+ 上下文，适合分析长财报

---

## 十三、可借鉴 Skills 调研（2026-06-01）

### 13.1 结论

没有发现可以直接解决 A 股 Agent Quant 的完整 skill，但有多类 skill 的流程、提示词结构和安全门禁值得吸收。建议**暂不安装**，先把可复用模式融入本项目的 Agent Foundry skills / subagents。

### 13.2 高价值参考

| Skill | 安装量 | 可借鉴点 | 适配方式 |
|------|--------|----------|----------|
| `wshobson/agents@backtesting-frameworks` | 11.2K | 防前视偏差、样本外、walk-forward、Monte Carlo、成本建模 | 加入 S3-S5 回测审查清单 |
| `stanleychanh/...@tushare-finance` | 4.3K | Tushare token 预检、API 分类选择、日期/代码标准化 | 作为 S8 情绪数据备选源模板 |
| `jeremylongshore/...@backtesting-trading-strategies` | 3.8K | 策略参数定义、网格搜索、收益曲线/交易日志/摘要输出 | 加入策略对比和报告格式 |
| `affaan-m/...@llm-trading-agent-security` | 2.8K | 把 prompt injection 当金融风险；隔离执行权限；simulation/dry-run | 加入 Agent 风控和工具权限门禁 |
| `0xhubed/agent-trading-arena@risk-management` | 1.5K | 入场前风险检查、单笔风险上限、市场阶段控制交易频率 | 改造成 A 股短线风控 Agent 策略 |
| `aradotso/trending-skills@daily-stock-analysis` | 1.4K | 每日分析报告、买卖/止损位、LiteLLM、多渠道通知、Dashboard | 借鉴 S12 每日报告结构 |
| `omer-metin/...@quantitative-research` | 1.7K | “backtest is always lying” 研究纪律、t-stat、Sharpe、过拟合质疑 | 加入 plan-reviewer/dev-reviewer 检查 |
| `blave-tw/...@blave-quant` | 1.7K | 所有交易/资金写操作必须当前对话明确 `CONFIRM` | 直接吸收为实盘安全门禁 |

### 13.3 应吸收为项目规则的模式

#### 回测研究纪律

- 每个策略必须区分训练期、验证期、样本外期。
- 每次回测报告必须显示手续费、滑点、最大回撤、胜率、盈亏比。
- 策略参数优化后必须做 walk-forward 或至少样本外验证。
- Agent 推荐策略时必须说明是否存在前视偏差、幸存者偏差、过拟合风险。

#### A 股数据接入预检

- 对 Tushare / AKShare / 腾讯等数据源建立统一 preflight：token、依赖、网络、字段格式、交易日。
- 所有 A 股代码统一成内部格式，输入输出时再转换。
- 日期统一 `YYYY-MM-DD` 存储，调用 Tushare 时转换为 `YYYYMMDD`。

#### Agent 交易安全门禁

- Agent 永远只推荐，不自动实盘下单。
- 未来如接入券商，任何真实下单/撤单/转账必须当前对话明确 `CONFIRM`。
- Prompt injection 是金融风险：新闻、社交媒体、公告、研报都视为不可信输入。
- 外部文本只能作为事实材料，不允许覆盖系统规则、风控规则或交易权限。

#### 每日报告结构

每日报告应固定包含：

```text
1. 市场情绪温度：冰点/修复/发酵/高潮/退潮
2. 涨停生态：涨停数、跌停数、炸板率、连板高度
3. 板块强度：Top 5 题材、资金流、助攻股
4. 龙头候选：Top 10，含龙头/跟风/补涨分类
5. 龙虎榜/新闻/公告/社交媒体摘要
6. 多空辩论：看多理由、看空风险
7. 人类决策问题：题材真假？阶段是否匹配？是否出手？
8. 风控建议：仓位、止损、禁止交易条件
```

### 13.4 不建议直接采用的部分

- Binance / crypto futures skills：偏加密货币，市场机制不同。
- Yahoo Finance skills：不适合 A 股核心数据。
- 通用 sentiment-analysis skills：缺少金融/A股语境。
- 低安装量 memory skills：质量和维护不确定，本项目已有 memory 体系。

---

## 十四、AKShare / 东方财富接口可用性专项调研（2026-06-01）

### 14.1 结论

AKShare 的 A 股情绪数据仍值得用，但**不能直接硬依赖 AKShare 单源**。更稳妥的方案是：

```text
业务代码 → 情绪数据 Provider 层 → AKShare / 直接东方财富 / curl_cffi / Tushare Pro fallback
```

短期可以继续尝试 AKShare，长期如果进入每日自动化或真实交易，应配置 Tushare Pro 或其他授权数据源作为稳定兜底。

### 14.2 已知失败原因

| 原因 | 说明 | 对项目影响 |
|------|------|------------|
| 东方财富接口变化 | endpoint、字段、分页参数随网页变化 | AKShare 版本落后时会失败 |
| TLS/JA3 指纹识别 | `requests`/`curl` 和真实浏览器 TLS 指纹不同 | Python 直接断连、`RemoteDisconnected` |
| Header/Cookie 缺失 | 缺少 UA、Referer、Accept-Language、Cookie | API 返回空或直接断连 |
| 代理/DNS 干扰 | Clash fake-ip、系统代理、境外 IP 质量 | 请求被路由到异常路径 |
| 频率/并发风控 | 短时间大量请求触发限制 | 日更任务需限速和退避 |

### 14.3 受影响的关键 AKShare 函数

| 数据 | AKShare 函数 | 底层来源 | 风险 |
|------|-------------|----------|------|
| 涨停池 | `stock_zt_pool_em` | `push2ex.eastmoney.com` | 高 |
| 昨日涨停池 | `stock_zt_pool_previous_em` | `push2ex.eastmoney.com` | 高 |
| 强势股池 | `stock_zt_pool_strong_em` | `push2ex.eastmoney.com` | 高 |
| 炸板池 | `stock_zt_pool_zbgc_em` | `push2ex.eastmoney.com` | 高 |
| 龙虎榜 | `stock_lhb_detail_em` | `datacenter-web.eastmoney.com` | 中高 |
| 龙虎榜统计 | `stock_lhb_stock_statistic_em` | `datacenter-web.eastmoney.com` | 中高 |
| 板块资金流 | `stock_sector_fund_flow_rank` | `push2.eastmoney.com` | 中高 |
| 板块资金流汇总 | `stock_sector_fund_flow_summary` | `push2.eastmoney.com` | 中高 |

### 14.4 可行解决方案分层

#### 第一层：最小立即修复

- 升级 AKShare 到最新版。
- 统一禁用环境代理或明确代理策略：`session.trust_env = False`。
- 添加浏览器 headers：`User-Agent`、`Referer`、`Accept`、`Accept-Language`。
- 使用 `requests.Session()`，先访问东方财富页面获取 cookie，再调用 API。
- 设置 timeout、指数退避、错误分类和本地缓存。

#### 第二层：项目内直接封装东方财富 HTTP Client

不要让业务代码直接调用 AKShare，而是封装：

```python
class EastMoneyHttpClient:
    def get_json(url, params, referer):
        # headers + session + cookie + retry + timeout + error classify
        ...
```

业务层只依赖：

```python
SentimentDataProvider.get_limit_up_pool(date)
SentimentDataProvider.get_dragon_tiger(date)
SentimentDataProvider.get_sector_flow(date)
```

这样后续 AKShare 失效时，只改 provider，不改策略和 Agent。

#### 第三层：curl_cffi / tls-client 浏览器指纹模拟

当普通 `requests` 仍然被断连时，可选启用：

```python
from curl_cffi import requests as crequests

session = crequests.Session(impersonate="chrome")
session.headers.update({
    "User-Agent": "Mozilla/5.0 ... Chrome/... Safari/537.36",
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
})
response = session.get(url, params=params, timeout=15)
```

注意：这属于更接近绕过反爬的方案，维护和合规风险更高，应做成可配置 fallback，而不是默认主路径。

#### 第四层：Tushare Pro 付费/积分兜底

| 数据 | Tushare 接口 | 积分门槛 |
|------|-------------|----------|
| 涨跌停/炸板 | `limit_list_d` | 5000 积分 |
| 龙虎榜 | `top_list` | 2000 积分 |
| 东方财富板块资金流 | `moneyflow_ind_dc` | 6000 积分 |

Tushare 的优势是字段稳定、历史回溯更可靠；缺点是积分/付费门槛。

### 14.5 推荐落地方案

S8 情绪数据层按 provider 链实现：

```text
LimitUpProvider:
  1. AKShareProvider
  2. EastMoneyDirectProvider
  3. CurlCffiEastMoneyProvider（可选开关）
  4. TushareProvider（用户提供 token 时启用）
```

关键设计：

- 每个 provider 输出统一 schema。
- 每次采集记录 provider 名称、原始字段、请求时间和失败原因。
- 成功结果写入 Parquet 缓存，后续优先读缓存，降低触发风控概率。
- Agent 只读取规范化数据，不接触爬虫细节。

### 14.6 合规和维护风险

- AKShare 官方定位偏学术研究，商业/实盘使用需自行承担风险。
- 东方财富非正式 API 无 SLA，字段和接口可随时变化。
- TLS 指纹模拟、cookie 复用、浏览器自动化可能违反目标站服务条款。
- 如果系统进入真实交易或长期自动化，建议采购授权数据源。

### 14.7 对开发计划的影响

- S8 不能只写 `AKShareGateway`，必须写成 `SentimentProvider` 抽象 + fallback 链。
- S8 需要新增 provider 健康检查和缓存。
- `TUSHARE_TOKEN` 应加入未来配置，但不是 MVP 必需。
- `curl_cffi` 不应立即加入依赖，先作为可选方案；确认普通 headers/session 不够后再启用。

### 14.8 本地实测验证（2026-06-01）

验证脚本：

```bash
uv run python scripts/probe_akshare_eastmoney.py
uv run python scripts/probe_eastmoney_sector_flow.py
```

环境：

- AKShare 版本：`1.18.64`
- 已设置 `PYTHONIOENCODING=utf-8` 避免中文列名乱码
- 第二轮探针清除了 `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY` 等环境代理变量

#### AKShare 情绪接口实测

| 接口 | 日期 | 结果 | 说明 |
|------|------|------|------|
| `stock_zt_pool_em` | 2026-05-29 | ✅ 49 行 | 涨停池可用 |
| `stock_zt_pool_zbgc_em` | 2026-05-29 | ✅ 38 行 | 炸板池可用 |
| `stock_zt_pool_dtgc_em` | 2026-05-29 | ✅ 50 行 | 跌停池可用 |
| `stock_lhb_detail_em` | 2026-05-29 | ✅ 94 行 | 历史龙虎榜可用 |
| `stock_zt_pool_em` | 2026-06-01 | ✅ 49 行 | 当前日期会返回最近交易日数据 |
| `stock_zt_pool_zbgc_em` | 2026-06-01 | ✅ 38 行 | 当前日期会返回最近交易日数据 |
| `stock_zt_pool_dtgc_em` | 2026-06-01 | ✅ 50 行 | 当前日期会返回最近交易日数据 |
| `stock_lhb_detail_em` | 2026-06-01 | ❌ `NoneType` | 当前日龙虎榜可能尚未发布或接口返回空 |
| `stock_sector_fund_flow_rank` | 今日/5日/10日 | ❌ `RemoteDisconnected` | 板块资金流仍不可用 |

#### 直接东方财富 endpoint 实测

涨停池底层 endpoint `push2ex.eastmoney.com/getTopicZTPool`：

| 方式 | 结果 | 说明 |
|------|------|------|
| `requests` 裸请求 | ✅ HTTP 200 | 能连通，但旧日期可能返回空 |
| `requests` + headers + 禁代理 | ✅ HTTP 200 | 可用 |
| `curl_cffi` Chrome 指纹 | ✅ HTTP 200 | 可用，速度更快 |

板块资金流底层 endpoint `push2.eastmoney.com/api/qt/clist/get`：

| 方式 | 结果 |
|------|------|
| `requests` 裸请求 | ❌ 断连 |
| `requests` + headers | ❌ 断连 |
| `requests.Session` + headers + 禁代理 | ❌ 断连 |
| `curl_cffi` Chrome 指纹 | ❌ 断连 |

### 14.9 验证后的修正判断

1. **涨停/炸板/跌停池：可以先用 AKShare。** 当前环境下 AKShare 1.18.64 可直接拿到数据。
2. **龙虎榜：历史日可用，当日可能需等发布。** 系统应允许“当前日无龙虎榜”而不是报错中断。
3. **板块资金流：不能依赖 AKShare/EastMoney 当前路径。** 即使 headers、禁代理、curl_cffi 都不够。
4. **S8 第一版应优先实现涨停生态 + 龙虎榜，板块资金流作为可选数据源。**
5. **板块资金流长期建议用 Tushare Pro `moneyflow_ind_dc` 或其他授权源兜底。**

### 14.10 对 S8 的具体落地调整

S8 第一版 Provider 优先级调整为：

```text
必须实现：
- LimitUpProvider：AKShare stock_zt_pool_em / zbgc / dtgc
- DragonTigerProvider：AKShare stock_lhb_detail_em，允许当日为空

可选/后续：
- SectorFlowProvider：Tushare Pro moneyflow_ind_dc 优先，AKShare 仅作为尝试源
- EastMoneyDirectProvider：优先用于涨停池 fallback，不再假设能解决板块资金流
```

S8 验收标准也应修正：涨停池、炸板池、跌停池、历史龙虎榜必须通过；板块资金流只要求 provider 接口存在，数据源可配置且失败不阻塞主流程。

### 14.11 全需求数据源覆盖验证（2026-06-01）

用户要求：Agent Quant 需求中的数据源能力都要测通。验证脚本：

```bash
$env:PYTHONIOENCODING='utf-8'
uv run python scripts/verify_data_requirements.py
```

验证结果：

```text
SUMMARY: total_checks=23, passed_checks=22, failed_optional_checks=1
required_capabilities=13
covered_capabilities=13
missing_capabilities=[]
```

#### 已测通能力矩阵

| 能力 | 可用数据源/函数 | 验证结果 |
|------|----------------|----------|
| 涨停生态 | `stock_zt_pool_em`、`stock_zt_pool_zbgc_em`、`stock_zt_pool_dtgc_em`、`stock_zt_pool_previous_em`、`stock_zt_pool_strong_em` | ✅ 全部可用 |
| 龙虎榜 | `stock_lhb_detail_em`（东方财富）、`stock_lhb_detail_daily_sina`（新浪） | ✅ 两路可用 |
| 题材/板块 | `stock_board_industry_name_ths`、`stock_board_concept_name_ths` | ✅ 同花顺源可用 |
| 板块强度/资金替代 | `stock_board_industry_summary_ths` | ✅ 可用，含净流入、上涨/下跌家数、领涨股 |
| 题材驱动事件 | `stock_board_concept_summary_ths` | ✅ 可用，含驱动事件、龙头股、成分股数量 |
| 板块异动/主力净流入替代 | `stock_board_change_em` | ✅ 可用，1000 行，含主力净流入和异动次数 |
| 社交/热度 | `stock_hot_search_baidu`、`stock_js_weibo_report` | ✅ 两路可用 |
| 新闻 | `stock_news_main_cx` | ✅ 财新资讯可用 |
| 公告 | `stock_notice_report`、`stock_individual_notice_report` | ✅ 全市场/个股公告可用 |
| 研报 | `stock_research_report_em` | ✅ 个股研报可用 |
| 宏观新闻 | `news_cctv` | ✅ 新闻联播文本可用 |
| 北向资金 | `stock_hsgt_fund_flow_summary_em`、`stock_hsgt_hist_em` | ✅ 摘要/历史可用 |
| 实时行情 | 腾讯 `qt.gtimg.cn` | ✅ 可用 |

#### 未通但已有替代的可选单源

| 失败项 | 失败原因 | 替代路径 |
|--------|----------|----------|
| `stock_sector_fund_flow_rank/hist/summary` | 东方财富 `push2.eastmoney.com` 断连 | 用 `stock_board_industry_summary_ths` + `stock_board_change_em` 覆盖板块强度/资金替代 |
| `stock_board_industry_name_em` / `stock_board_concept_name_em` | 东方财富断连 | 用同花顺 `*_ths` 版本 |
| `stock_hot_rank_em` | 东方财富人气榜断连 | 用百度热搜 + 微博股票报告 |
| `stock_news_em` | AKShare 清洗阶段正则兼容问题，且 direct 搜索返回类型不稳定 | 用财新资讯 + 公告 + 研报覆盖文本输入 |
| `news_economic_baidu` | Baidu cookie/TLS 错误 | 非核心，宏观新闻用 `news_cctv` 暂代 |

### 14.12 对产品需求的修正

当前不再要求“某个具体接口必须通”，而要求“每类 Agent Quant 数据能力至少有一个已验证 provider”。已覆盖的 13 类能力足以支持：

- 扫描 5000 只股票
- 找龙头
- 计算情绪指标
- 判断涨停生态
- 读取龙虎榜
- 获取题材/板块和驱动事件
- 获取公告、研报、新闻、热度和北向资金
- 使用实时行情做模拟实盘

S8 实现时应基于这个可通矩阵，而不是继续强行依赖失败的东方财富板块资金流接口。

---

## 信息来源

- AKShare: https://github.com/akfamily/akshare
- TuShare: https://tushare.pro
- vnpy: https://github.com/vnpy/vnpy
- qlib: https://github.com/microsoft/qlib
- rqalpha: https://github.com/ricequant/rqalpha
- NautilusTrader: https://github.com/nautechsystems/nautilus_trader
- QuantConnect/Lean: https://github.com/QuantConnect/Lean
- backtrader: https://github.com/mementum/backtrader
- FinRL-X/Trading: https://github.com/AI4Finance-Foundation/FinRL-Trading
- FinGPT: https://github.com/AI4Finance-Foundation/FinGPT
- FinRobot: https://github.com/AI4Finance-Foundation/FinRobot
- Qlib: https://github.com/microsoft/QLib
- RD-Agent: https://github.com/microsoft/RD-Agent
