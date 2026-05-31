# 开发计划

版本：v1.0
日期：2026-05-31
状态：待审查
基于：Product.md（审查通过）

---

## 切片总览

| 切片 | 名称 | 用户可见目标 | 预计代码量 | 依赖 |
|------|------|-------------|-----------|------|
| S1 | 数据就绪 | 能下载 A 股数据并查看 | ~400 行 | 无 |
| S2 | 因子计算 | 能用表达式计算因子 | ~800 行 | S1 |
| S3 | 第一次回测 | 能跑通买入持有回测 | ~600 行 | S1 |
| S4 | 真实策略 | 双均线策略完整回测 | ~500 行 | S2, S3 |
| S5 | A 股规则 | 精确模拟交易规则 | ~500 行 | S4 |
| S6 | 模拟实盘 | 能切换到模拟实盘模式 | ~500 行 | S5 |
| S7 | 可视化 | Streamlit 仪表盘完整闭环 | ~500 行 | S6 |

**执行顺序**：S1 → S2 → S3 → S4 → S5 → S6 → S7

S2 和 S3 可并行开发（无互相依赖），但为降低风险建议串行。

---

## 切片 1：数据就绪

### 用户可见目标
运行一条命令，下载指定股票的日线数据，查看数据摘要和 K 线图。

### 涉及文件
```
新增：
├── pyproject.toml                    # uv 项目配置
├── src/quant_lab/__init__.py
├── src/quant_lab/config.py           # 全局配置
├── src/quant_lab/data/__init__.py
├── src/quant_lab/data/schemas.py     # 数据模型（Pydantic）
├── src/quant_lab/data/gateway.py     # BaseGateway 抽象
├── src/quant_lab/data/akshare_gateway.py  # AKShare 实现
├── src/quant_lab/data/storage.py     # Parquet 读写
├── scripts/fetch_data.py             # 数据采集脚本
└── data/                             # 数据目录（.gitignore）
```

### 数据流
```
用户运行: uv run python scripts/fetch_data.py --symbol 600000 --start 2024-01-01 --end 2024-12-31
    ↓
AKShareGateway.fetch_daily(symbol, start, end) → DataFrame
    ↓
Storage.save(df, path="data/raw/cn_stock/daily/SH600000/") → Parquet 文件
    ↓
Storage.load(path) → DataFrame
    ↓
打印摘要：行数、列名、日期范围、最新价格
```

### 验收故事
```
Given 用户运行 fetch_data.py --symbol 600000 --start 2024-01-01 --end 2024-12-31
When  脚本执行完成
Then  Parquet 文件存在于 data/raw/cn_stock/daily/SH600000/
And   文件包含约 243 条记录
And   字段包含 date, open, high, low, close, volume
And   终端输出数据摘要（行数、日期范围、最新收盘价）
```

### 测试策略
- 单元测试：`test_schemas.py`（数据模型验证）、`test_storage.py`（Parquet 读写）
- 集成测试：`test_akshare_gateway.py`（实际网络请求，标记为 slow）
- 验证命令：`uv run pytest tests/test_data/ -v`

### 验证命令
```bash
# 1. 项目初始化
uv init && uv add polars pyarrow akshare pydantic loguru
uv run python -c "import quant_lab"

# 2. 下载数据
uv run python scripts/fetch_data.py --symbol 600000 --start 2024-01-01 --end 2024-12-31

# 3. 检查文件
ls data/raw/cn_stock/daily/SH600000/

# 4. 运行测试
uv run pytest tests/test_data/ -v
```

### 依赖
- 无前置依赖

### 风险
- AKShare 接口可能变动 → 抽象 Gateway 层，换源只改一个文件
- 网络请求可能超时 → 添加重试机制（3 次）

### 回滚方式
删除项目目录即可，无外部依赖。

---

## 切片 2：因子计算

### 用户可见目标
输入一个 DSL 表达式（如 `Mean($close, 20)`），系统计算并输出因子值。

### 涉及文件
```
新增：
├── src/quant_lab/expression/__init__.py
├── src/quant_lab/expression/parser.py      # DSL 解析器
├── src/quant_lab/expression/compiler.py    # AST → Polars 编译器
├── src/quant_lab/expression/operators.py   # 运算符定义（20 个）
├── src/quant_lab/expression/cache.py       # 缓存（可选，MVP 简化）
└── tests/test_expression/
    ├── test_parser.py
    ├── test_compiler.py
    └── test_operators.py
```

### 数据流
```
用户输入: "Mean($close, 20)"
    ↓
Parser.parse("Mean($close, 20)") → AST: CallNode("Mean", [FeatureNode("close"), 20])
    ↓
Compiler.compile(ast) → pl.col("close").rolling_mean(20)
    ↓
df.with_columns(expr.alias("Mean($close, 20)")) → 带因子列的 DataFrame
    ↓
输出：前 19 行为 null，第 20 行起为 20 日均值
```

### 验收故事
```
Given 用户输入 DSL 表达式 "Mean($close, 20)"
When  系统编译并执行
Then  返回 Polars Series，长度与输入一致
And   前 19 个值为 null
And   第 20 个值 = 前 20 日收盘价的算术平均
And   结果与 pandas rolling(20).mean() 一致

Given 用户输入嵌套表达式 "Rank(Mean($close, 20), 60)"
When  系统编译并执行
Then  返回滚动排名值（0-1 之间）
```

### 测试策略
- 单元测试：每个运算符独立测试（与 pandas 结果对比）
- 解析器测试：嵌套调用、错误输入、边界条件
- 验证命令：`uv run pytest tests/test_expression/ -v`

### 验证命令
```bash
# 1. 安装依赖
uv add polars

# 2. 运行表达式测试
uv run pytest tests/test_expression/ -v

# 3. 手动验证
uv run python -c "
from quant_lab.expression.parser import Parser
from quant_lab.expression.compiler import Compiler
import polars as pl

# 加载数据
df = pl.read_parquet('data/raw/cn_stock/daily/SH600000/*.parquet')

# 计算因子
ast = Parser.parse('Mean(\$close, 20)')
expr = Compiler.compile(ast)
result = df.with_columns(expr.alias('factor'))
print(result.select(['date', 'close', 'factor']).tail(5))
"
```

### 依赖
- S1（需要数据文件）

### 风险
- Polars 滚动窗口 API 与 pandas 有细微差异 → 以 Polars 行为为准，测试中注明
- DSL 解析器边界情况多 → 先支持核心语法，逐步扩展

### 回滚方式
删除 `src/quant_lab/expression/` 目录。

---

## 切片 3：第一次回测

### 用户可见目标
运行一个"买入持有"策略的回测，看到收益曲线和基础指标。

### 涉及文件
```
新增：
├── src/quant_lab/engine/__init__.py
├── src/quant_lab/engine/core.py           # 引擎核心循环
├── src/quant_lab/engine/matching.py       # 撮合引擎（简化版）
├── src/quant_lab/engine/portfolio.py      # 持仓管理
├── src/quant_lab/engine/account.py        # 账户管理
├── src/quant_lab/analytics/__init__.py
├── src/quant_lab/analytics/metrics.py     # 绩效指标
├── src/quant_lab/strategy/__init__.py
├── src/quant_lab/strategy/base.py         # 策略基类
├── src/quant_lab/strategy/examples/buy_and_hold.py  # 买入持有策略
├── scripts/run_backtest.py                # 回测脚本
└── tests/test_engine/
    ├── test_matching.py
    ├── test_portfolio.py
    └── test_metrics.py
```

### 数据流
```
用户运行: uv run python scripts/run_backtest.py --symbol 600000 --start 2024-01-01 --end 2024-12-31
    ↓
Storage.load() → 日线 DataFrame
    ↓
Engine.run(strategy=BuyAndHold, data=df)
    ↓
  逐 bar 循环:
    strategy.on_bar(bar) → 生成买入信号
    matching.match(order, bar) → 生成成交
    portfolio.update(trade) → 更新持仓
    account.update(bar) → 更新资金
    ↓
PerformanceAnalyzer.calculate(equity_curve) → 指标
    ↓
输出：总收益率、年化收益率、最大回撤、夏普比率
```

### 验收故事
```
Given 股票 600000，时间 2024-01-01 至 2024-12-31，初始资金 100 万
When  运行买入持有策略回测
Then  系统输出收益曲线数据
And   输出总收益率（应接近该股票全年涨跌幅）
And   输出最大回撤（应为正数）
And   输出夏普比率
And   交易记录包含：第 1 天买入，最后 1 天卖出（或持有到最后）
```

### 测试策略
- 单元测试：撮合引擎（价格/数量正确）、持仓管理（买入/卖出更新）、绩效指标（已知数据验算）
- 验证命令：`uv run pytest tests/test_engine/ -v`

### 验证命令
```bash
# 1. 运行回测
uv run python scripts/run_backtest.py --symbol 600000 --start 2024-01-01 --end 2024-12-31

# 2. 预期输出
# 总收益率: XX.XX%
# 年化收益率: XX.XX%
# 最大回撤: -XX.XX%
# 夏普比率: X.XX

# 3. 运行测试
uv run pytest tests/test_engine/ -v
```

### 依赖
- S1（需要数据文件）

### 风险
- 买入持有策略太简单，无法验证撮合逻辑 → S4 用双均线策略补充验证
- 绩效指标计算可能有边界情况 → 用已知数据手算验证

### 回滚方式
删除 `src/quant_lab/engine/` 和 `src/quant_lab/analytics/` 目录。

---

## 切片 4：真实策略

### 用户可见目标
运行双均线策略（5 日/20 日金叉死叉）回测，看到完整的交易记录和绩效指标。

### 涉及文件
```
新增/修改：
├── src/quant_lab/strategy/examples/dual_ma.py    # 双均线策略
├── src/quant_lab/engine/matching.py               # 完善撮合逻辑（限价单）
├── src/quant_lab/engine/rules.py                  # A 股规则（基础版：手续费）
└── tests/test_strategy/
    └── test_dual_ma.py
```

### 数据流
```
双均线策略逻辑：
  on_bar(bar):
    prices.append(bar.close)
    if len(prices) >= 20:
      short_ma = mean(prices[-5:])
      long_ma = mean(prices[-20:])
      if short_ma > long_ma and no_position:
        buy(100 股)
      elif short_ma < long_ma and has_position:
        sell(all)
```

### 验收故事
```
Given 双均线策略（5/20），股票 600000，时间 2024-01-01 至 2024-12-31
When  运行回测
Then  系统输出完整绩效报告（收益率、夏普、回撤、胜率、盈亏比）
And   交易记录中每笔订单包含：时间、方向、价格、数量、手续费
And   手续费计算正确（佣金万 2.5，最低 5 元；印花税千 1 仅卖出）
And   交易次数 > 0（有金叉死叉信号触发交易）
```

### 测试策略
- 单元测试：双均线信号生成（已知数据验证金叉/死叉时间点）
- 手续费测试：买入 10 万股票，佣金应为 25 元（> 5 元最低）
- 验证命令：`uv run pytest tests/test_strategy/ -v`

### 验证命令
```bash
# 1. 运行双均线回测
uv run python scripts/run_backtest.py --strategy dual_ma --symbol 600000 --start 2024-01-01 --end 2024-12-31

# 2. 预期输出
# 总收益率: XX.XX%
# 交易次数: N 笔
# 胜率: XX.XX%
# 盈亏比: X.XX

# 3. 运行测试
uv run pytest tests/test_strategy/ -v
```

### 依赖
- S2（表达式引擎，用于计算均线）
- S3（回测引擎基础）

### 风险
- 双均线策略可能全年无交易（震荡市）→ 选择有明显趋势的时间段测试
- 手续费计算边界（最低 5 元）→ 专门的测试用例

### 回滚方式
删除 `src/quant_lab/strategy/examples/dual_ma.py`。

---

## 切片 5：A 股规则

### 用户可见目标
回测引擎精确模拟 A 股交易规则，违反规则的订单被正确拒绝。

### 涉及文件
```
新增/修改：
├── src/quant_lab/engine/rules.py          # 完整 A 股规则引擎
├── src/quant_lab/engine/matching.py       # 撮合引擎集成规则检查
└── tests/test_engine/
    └── test_rules.py
```

### 规则清单
| 规则 | 实现方式 |
|------|----------|
| T+1 | Position.buy_date 记录买入日，卖出时检查 available |
| 涨跌停 | 根据 pre_close 计算上下限，订单价格必须在范围内 |
| 手续费 | 佣金万 2.5（最低 5 元）+ 印花税千 1（卖出）+ 过户费十万分之二 |
| 最小单位 | 主板 100 股整数倍，科创板 200 股 |
| 撮合模式 | 支持开盘价/收盘价/VWAP 三种 |

### 验收故事
```
Given 策略尝试在涨停价以上买入
When  撮合引擎处理订单
Then  订单被拒绝，原因："买入价格超过涨停价 XX.XX"

Given 策略尝试卖出当日买入的股票
When  撮合引擎处理订单
Then  订单被拒绝，原因："可卖数量不足"

Given 策略买入 150 股主板股票
When  撮合引擎处理订单
Then  订单被拒绝，原因："交易数量必须是 100 的整数倍"

Given 策略以收盘价买入 100 股，佣金计算
When  成交价格 10 元
Then  佣金 = max(10 * 100 * 0.00025, 5) = 5 元（最低佣金）

Given 撮合模式设置为 VWAP
When  当日 high=10.5, low=9.5, close=10.0
Then  成交价 = (10.5 + 9.5 + 10.0) / 3 = 10.0
```

### 测试策略
- 每条规则至少 2 个测试用例（通过 + 拒绝）
- 手续费边界测试（小额触发最低佣金、大额正常计算）
- 三种撮合模式各一个测试
- 验证命令：`uv run pytest tests/test_engine/test_rules.py -v`

### 验证命令
```bash
# 1. 运行规则测试
uv run pytest tests/test_engine/test_rules.py -v

# 2. 运行带规则的回测
uv run python scripts/run_backtest.py --strategy dual_ma --symbol 600000 --start 2024-01-01 --end 2024-12-31

# 3. 检查交易记录中的手续费是否正确
```

### 依赖
- S4（需要策略和撮合引擎）

### 风险
- 涨跌停价格四舍五入可能有精度问题 → 使用 round(x, 2)
- 科创板/创业板判断需要股票代码映射 → MVP 先只支持主板

### 回滚方式
回退 `rules.py` 到基础版本。

---

## 切片 6：模拟实盘

### 用户可见目标
切换到模拟实盘模式，系统用最近的行情数据驱动策略运行，实时查看持仓和资金变化。

### 涉及文件
```
新增/修改：
├── src/quant_lab/data/akshare_gateway.py    # 添加实时行情方法
├── src/quant_lab/engine/core.py             # 支持 backtest/live 模式切换
├── src/quant_lab/engine/broker.py           # SimBroker（模拟交易网关）
└── tests/test_engine/
    └── test_broker.py
```

### 数据流
```
模式切换：
  engine = Engine(mode='live')  # 或 mode='backtest'

模拟实盘流程：
  AKShareGateway.get_latest_bar(symbol) → 最新行情
    ↓
  strategy.on_bar(bar) → 信号
    ↓
  broker.submit_order(order) → 撮合
    ↓
  portfolio.update(trade) → 持仓
    ↓
  实时打印：持仓、资金、浮动盈亏
```

### 验收故事
```
Given 用户切换到模拟实盘模式，初始资金 100 万
When  策略生成买入信号
Then  系统以当日收盘价撮合（默认模式）
And   持仓更新，显示浮动盈亏
And   资金扣减正确（含手续费和滑点）

Given 用户在回测模式运行双均线策略
When  切换到模拟实盘模式
Then  同一套策略代码无需修改即可运行
And   撮合逻辑、手续费、T+1 规则与回测一致
```

### 测试策略
- SimBroker 单元测试：下单/撤单/持仓更新
- 模式切换测试：同一策略在两种模式下运行
- 验证命令：`uv run pytest tests/test_engine/test_broker.py -v`

### 验证命令
```bash
# 1. 运行模拟实盘测试
uv run pytest tests/test_engine/test_broker.py -v

# 2. 手动测试模拟实盘
uv run python -c "
from quant_lab.engine.core import Engine
from quant_lab.strategy.examples.dual_ma import DualMAStrategy

engine = Engine(mode='live', initial_capital=1000000)
engine.set_strategy(DualMAStrategy(short=5, long=20))
engine.run(symbol='600000', days=5)  # 模拟 5 天
print(engine.account.summary())
"
```

### 依赖
- S5（A 股规则引擎）

### 风险
- AKShare 实时行情接口可能不稳定 → 添加异常处理和重试
- 模拟实盘需要等待行情，测试不方便 → 提供"快速模式"用历史数据模拟

### 回滚方式
删除 `broker.py`，引擎回退到仅回测模式。

---

## 切片 7：可视化

### 用户可见目标
打开浏览器，通过 Streamlit 仪表盘完成"选择股票 → 运行回测 → 查看结果"的完整闭环。

### 涉及文件
```
新增：
├── app/Home.py                    # 入口页面
├── app/pages/
│   ├── 1_数据浏览.py              # K 线图、数据摘要
│   ├── 2_因子编辑.py              # DSL 表达式输入、因子可视化
│   ├── 3_回测运行.py              # 策略配置、运行回测
│   ├── 4_绩效分析.py              # 收益曲线、指标表格
│   └── 5_模拟实盘.py              # 模拟实盘控制台
└── tests/test_app/
    └── test_pages.py              # 页面加载测试
```

### 页面功能

**1_数据浏览.py**
- 股票代码输入框
- 时间范围选择器
- K 线图（Plotly candlestick）
- 数据摘要表格

**2_因子编辑.py**
- DSL 表达式输入框
- 实时计算并展示因子值折线图
- 因子统计（均值、标准差、最大最小值）

**3_回测运行.py**
- 策略选择（下拉框：双均线、买入持有）
- 参数配置（短期窗口、长期窗口）
- 股票选择、时间范围、初始资金
- 撮合模式选择（开盘价/收盘价/VWAP）
- 运行按钮
- 运行结果：收益曲线图 + 指标卡片

**4_绩效分析.py**
- 指标卡片：总收益率、夏普、最大回撤、胜率
- 收益曲线图（与沪深 300 对比）
- 交易记录表格
- 月度收益热力图

**5_模拟实盘.py**
- 启动/停止按钮
- 实时持仓表格
- 实时资金信息
- 最近交易记录

### 验收故事
```
Given 用户运行 uv run streamlit run app/Home.py
When  浏览器打开 http://localhost:8501
Then  可以看到 5 个页面导航

Given 用户在"回测运行"页面选择双均线策略、600000、2024 年
When  点击"运行回测"按钮
Then  页面展示收益曲线图
And   展示夏普比率、最大回撤、总收益率等指标
And   展示交易记录表格

Given 用户在"数据浏览"页面输入 600000
When  选择时间范围 2024-01-01 至 2024-12-31
Then  展示 K 线图
And   展示数据摘要（行数、日期范围）
```

### 测试策略
- 页面加载测试：每个页面能正常渲染（不报错）
- 集成测试：完整回测流程通过 Streamlit 运行
- 验证命令：`uv run pytest tests/test_app/ -v`

### 验证命令
```bash
# 1. 安装 Streamlit
uv add streamlit plotly

# 2. 启动应用
uv run streamlit run app/Home.py

# 3. 浏览器打开 http://localhost:8501
# 4. 手动验证每个页面

# 5. 运行测试
uv run pytest tests/test_app/ -v
```

### 依赖
- S6（完整的回测和模拟实盘功能）

### 风险
- Streamlit 性能限制（大数据量卡顿）→ 数据量控制在单股票日线级别
- Plotly K 线图配置复杂 → 使用 plotly 内置 candlestick 图表

### 回滚方式
删除 `app/` 目录。核心功能通过 CLI 脚本仍可用。

---

## 验证命令汇总

```bash
# 全量测试
uv run pytest tests/ -v

# 单切片测试
uv run pytest tests/test_data/ -v       # S1
uv run pytest tests/test_expression/ -v # S2
uv run pytest tests/test_engine/ -v     # S3, S4, S5, S6
uv run pytest tests/test_strategy/ -v   # S4
uv run pytest tests/test_app/ -v        # S7

# 完整闭环验证
uv run python scripts/fetch_data.py --symbol 600000 --start 2024-01-01 --end 2024-12-31
uv run python scripts/run_backtest.py --strategy dual_ma --symbol 600000 --start 2024-01-01 --end 2024-12-31
uv run streamlit run app/Home.py
```

---

## 风险总览

| 风险 | 影响 | 规避措施 |
|------|------|----------|
| AKShare 接口变动 | S1 数据采集失败 | Gateway 抽象层，换源只改一个文件 |
| Polars API 差异 | S2 因子计算结果不一致 | 以 Polars 行为为准，测试注明差异 |
| 撮合逻辑复杂度 | S4/S5 边界情况多 | 逐条规则独立测试，手算验证 |
| Streamlit 性能 | S7 大数据量卡顿 | 控制数据量，使用缓存 |
| 开发周期过长 | 整体延期 | 严格按切片交付，每切片独立验证 |
