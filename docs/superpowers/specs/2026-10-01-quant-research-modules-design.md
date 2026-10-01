# A 股量化研究模块化设计

## 目标

把现有“每课一个完整脚本”的项目逐步整理为可复用的 A 股因子研究代码。第一版建立 Data、Factor、Signal、
Portfolio、Backtest、Metrics 六个模块及稳定的数据接口，使研究者可以替换某一部分，而不必重写整个流程。

成功标准如下：

- 正式代码可以通过 `a_share_quant` Python 包导入；
- 六个模块各自只有清楚的职责，并通过约定字段交换数据；
- 20 日动量和等权选股可以使用新模块表达；
- 信号日期、执行日期、目标持仓和实际持仓保持明确区分；
- 每个模块能够独立测试，并有一个小型端到端测试验证数据流；
- 现有 `lessons/` 教学脚本及其结果继续保留，后续按学习进度逐步迁移。

本设计不连接真实券商，不下真实订单，也不接入实时行情。第一版不实现事件驱动交易引擎、数据库、分布式计算、
图形界面或多账户管理。

## 方案选择

采用 `src` 布局：正式包放在 `src/a_share_quant/`，测试继续放在 `tests/`。与把模块直接放在仓库根目录相比，
`src` 布局能防止测试意外导入工作目录中的同名文件，也更接近可安装 Python 包的结构。与立即建立多层子包相比，
第一版只使用六个平级模块，便于学习和查看；当单个模块职责明显增多时再拆分子包。

计划目录如下：

```text
src/
└── a_share_quant/
    ├── __init__.py
    ├── data.py
    ├── factor.py
    ├── signal.py
    ├── portfolio.py
    ├── backtest.py
    └── metrics.py
tests/
├── test_data.py
├── test_factor.py
├── test_signal.py
├── test_portfolio.py
├── test_backtest.py
├── test_metrics.py
└── test_research_pipeline.py
```

实现时增加最小的项目配置，使 `src/a_share_quant` 可以在开发环境中导入。现有 `lessons/`、`data/` 和 `result/`
目录保持原用途。

## 数据契约

模块以 Pandas DataFrame 交换批量数据。所有日期列使用 Pandas 日期类型，股票代码使用字符串，百分比和权重使用
小数形式，例如 `5%` 保存为 `0.05`。同一张表中 `(date, code)` 或其对应业务键必须唯一。

### 行情表

`data.py` 输出的第一版行情表至少包含：

| 字段 | 含义 |
| --- | --- |
| `date` | 交易日期 |
| `code` | 保留前导零的股票代码 |
| `open` | 当日开盘价 |
| `close` | 当日收盘价 |
| `can_trade` | 当日是否允许本教学模型尝试成交 |

价格复权口径由数据来源或调用配置明确说明。因子研究使用口径一致的复权价格；模拟成交价格必须使用符合成交假设的
价格字段。第一版 `can_trade` 是简化接口，后续处理涨跌停买卖方向时可以扩展为 `can_buy` 和 `can_sell`，但不能
在没有定义迁移规则时静默改变字段含义。

### 因子表

`factor.py` 输出：

| 字段 | 含义 |
| --- | --- |
| `date` | 因子能够在收盘后确定的日期 |
| `code` | 股票代码 |
| `factor_value` | 因子值，缺少足够历史数据时为 `NaN` |

统一列名让 Signal 模块可以在不读取因子内部实现的情况下替换动量、价值或质量因子。

### 目标权重表

`signal.py` 输出：

| 字段 | 含义 |
| --- | --- |
| `signal_date` | 目标产生日期 |
| `code` | 股票代码 |
| `target_weight` | 该股票的目标资金权重 |

同一信号日期内目标权重不得为负，总和不得超过 `1`。未使用的权重表示现金。目标表不包含“已经成交”的含义。

### 回测输出

`backtest.py` 返回 `BacktestResult`，其中包含三张表：

- `equity`：日期、现金、持仓市值、总资产和标准化净值；
- `positions`：日期、股票代码、实际数量、可卖数量、市值和实际权重；
- `trades`：信号日期、执行日期、股票代码、方向、成交数量、成交价格、成交金额、费用和成交状态。

未成交订单必须在交易记录中保留状态或原因，不能通过修改实际持仓来伪造成交。

## 模块职责与接口

### Data

```python
load_daily_data(path) -> pd.DataFrame
validate_daily_data(data) -> None
```

`load_daily_data()` 负责类型转换、排序和基础字段整理。`validate_daily_data()` 检查必要字段、业务键重复、价格有效性、
日期类型和股票代码类型。Data 不计算因子，不选择股票。

### Factor

```python
calculate_momentum(data, window=20) -> pd.DataFrame
```

函数在每只股票内部按日期排序，使用口径一致的收盘价计算动量。`window=20` 需要 21 个有效价格；不足的记录保留
`NaN`。Factor 不读取未来收益、目标权重或回测结果。

### Signal

```python
generate_top_n_targets(factors, top_n=2) -> pd.DataFrame
```

函数在每个有效信号日期内按 `factor_value` 降序选择前 `top_n` 只股票，并生成等权目标。并列值使用预先固定、可复现
的次级排序规则。Signal 只产生目标，不决定执行日期或成交结果。

### Portfolio

```python
build_orders(current_account, targets, prices) -> pd.DataFrame
apply_fills(current_account, fills) -> PortfolioState
```

`PortfolioState` 保存现金、实际持仓数量和可卖数量。`build_orders()` 根据当前账户价值与目标权重计算调整需求；
`apply_fills()` 只接受 Backtest 已判定成交的记录，按成交金额和费用更新账户。未成交订单不能改变账户。

### Backtest

```python
run_backtest(market_data, targets, initial_cash, cost_config) -> BacktestResult
```

Backtest 按交易日期推进：使用前一可知时点产生的目标，寻找严格晚于 `signal_date` 的执行日期，检查 `can_trade`，
计算模拟成交价及费用，生成成交记录，再调用 Portfolio 更新账户。每个估值日完成后记录实际持仓和净值。它负责
协调时间顺序，不重新计算因子排名。

第一版使用已有教学规则：收盘后目标最早在下一交易日尝试执行；交易受阻时实际持仓保持不变。佣金、印花税和滑点
通过 `cost_config` 提供，具体费率不得散落在多个模块中。

### Metrics

```python
calculate_metrics(backtest_result) -> dict[str, float]
```

第一版计算累计收益和最大回撤。Metrics 只读取回测输出，不修改成交记录、持仓或净值。后续可以在保持现有字段含义
的前提下增加基准收益、换手率和报告输出。

## 数据流与依赖方向

```text
CSV ──> Data ──> 行情表 ──> Factor ──> 因子表 ──> Signal ──> 目标权重
              └──────────────────────────────> Backtest <───┘
                                                   │
                                                   ├──调用──> Portfolio
                                                   │             │
                                                   <──账户状态────┘
                                                   │
                                    净值、实际持仓、交易记录
                                                   │
                                                   v
                                                Metrics
```

允许的依赖方向是上图所示的数据流。Factor 不导入 Backtest，Metrics 不导入 Signal 或修改 Portfolio。Backtest 可以
调用 Portfolio 的公开接口，但 Portfolio 不反过来启动 Backtest，从而避免循环依赖。

## 错误处理

- 缺少必要字段、业务键重复、权重非法和初始资金非正时，立即抛出带具体字段或日期信息的 `ValueError`；
- 动量历史不足属于正常研究结果，对应因子值保留 `NaN`，不作为程序错误；
- 某日没有有效因子时，Signal 不生成该日目标记录，Backtest 当日不调仓并保持原实际持仓；
- 不可交易属于模拟结果，记录未成交状态并保持实际账户不变；
- 中间估值价格缺失不能自动填成零，应报告数据问题或按照明确的估值规则处理；
- 所有公开函数不应原地修改调用者传入的 DataFrame，避免模块之间产生隐蔽副作用。

## 测试策略

每个模块使用小型虚构数据测试关键边界：

- Data：类型转换、排序、前导零、重复键和无效价格；
- Factor：按股票独立计算、21 个价格才产生首个 20 日动量、缺失价格不自动填补；
- Signal：同日排名、等权目标、并列规则、无效因子排除和权重合计；
- Portfolio：只按成交记录更新、买卖现金方向、费用及未成交不改变持仓；
- Backtest：下一交易日执行、停牌不成交、信号日期与执行日期分离；
- Metrics：累计收益、历史高点和最大回撤；
- 端到端测试：从一小段行情生成动量、目标、成交和净值，并确认结果可重复。

先写会失败的行为测试，再实现满足接口的最小代码。现有教学测试继续运行，确保模块化过程没有破坏已完成课程。

## 分步落地

实现按小任务推进：

1. 建立可导入的包结构与 Data 模块；
2. 迁移 20 日动量到 Factor，并实现 Signal 的前 N 名等权目标；
3. 实现 Portfolio 状态和成交更新；
4. 实现最小 Backtest 时间循环与交易成本；
5. 实现 Metrics 和端到端测试；
6. 在后续独立任务中加入配置文件、结果文件和研究报告。

每一步完成概念、代码和验收后再进入下一步，符合项目既定教学规则。
