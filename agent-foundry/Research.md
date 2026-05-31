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

## 信息来源

- AKShare: https://github.com/akfamily/akshare
- TuShare: https://tushare.pro
- vnpy: https://github.com/vnpy/vnpy
- qlib: https://github.com/microsoft/qlib
- rqalpha: https://github.com/ricequant/rqalpha
- NautilusTrader: https://github.com/nautechsystems/nautilus_trader
- QuantConnect/Lean: https://github.com/QuantConnect/Lean
- backtrader: https://github.com/mementum/backtrader
