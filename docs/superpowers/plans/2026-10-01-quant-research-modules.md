# A 股量化研究六模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可导入、可测试的 Data、Factor、Signal、Portfolio、Backtest、Metrics 六模块，并用虚构数据跑通一条无未来数据泄漏的 20 日动量等权回测链路。

**Architecture:** 正式代码使用 `src/a_share_quant/` 平级模块，通过字段固定的 Pandas DataFrame 交换数据。Backtest 负责时间顺序和成交协调，Portfolio 只按成交记录更新账户，Metrics 只读取结果。

**Tech Stack:** Python 3.10+、Pandas、标准库 `dataclasses` 与 `unittest`、setuptools `src` 布局

**Spec:** `docs/superpowers/specs/2026-10-01-quant-research-modules-design.md`

## Global Constraints

- 不连接真实券商，不下真实订单，不接入实时行情。
- 保留现有 `lessons/`、`data/`、`result/` 及已有测试的行为。
- 股票代码使用字符串；日期使用 Pandas 日期类型；权重和收益率使用小数。
- 公开函数复制传入的 DataFrame，不原地修改调用者数据。
- 收盘后目标最早在下一交易日尝试执行；未成交订单不改变实际持仓。
- 第一版 `can_trade` 同时控制买卖；方向化的 `can_buy`、`can_sell` 留待后续扩展。
- 测试使用虚构数据和 `unittest`，每项实现遵循先失败测试、后最小实现的顺序。
- Git 提交步骤作为检查点保留；实际提交前遵循用户当时的明确授权。

## Review Focus

- CSV 股票代码含前导零：`load_daily_data()` 必须保留为字符串，Task 2 覆盖。
- 重复 `(date, code)`、无效日期或非正价格：Data 必须明确报错，Task 2 覆盖。
- 因子历史中间缺失：不得自动填补价格，Task 3 覆盖。
- 同日因子并列跨越选择边界：必须按 `code` 升序稳定决定，Task 3 覆盖。
- 交易受阻、T+1 或成交费用导致现金不足：不能伪造成交或产生负现金，Task 5 覆盖。

---

### Task 1: 建立可导入的 `src` 包

**Files:**
- Create: `pyproject.toml`
- Create: `src/a_share_quant/__init__.py`
- Create: `tests/test_package_import.py`
- Modify: `scripts/init_env.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: Python 3.10+ 和现有 `requirements.txt`
- Produces: 可执行 `import a_share_quant` 的开发环境；包版本 `__version__ = "0.1.0"`

- [ ] **Step 1: 写包导入失败测试**

在 `tests/test_package_import.py` 中断言导入成功且 `a_share_quant.__version__ == "0.1.0"`。

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest tests/test_package_import.py -v`
Expected: FAIL，原因是找不到 `a_share_quant`。

- [ ] **Step 3: 添加最小包配置**

创建使用 setuptools 的 `pyproject.toml`，设置 `requires-python = ">=3.10"`、版本 `0.1.0` 和 `src` 包发现；在 `__init__.py` 暴露同一版本号。

- [ ] **Step 4: 让初始化脚本安装当前项目**

在依赖安装后执行 `python -m pip install --editable <ROOT> --no-deps`，再用子进程同时验证 Pandas 和 `a_share_quant` 可导入；README 说明初始化会安装可编辑包。

- [ ] **Step 5: 安装并验证包测试**

Run: `.venv/bin/python -m pip install --editable . --no-deps`
Run: `.venv/bin/python -m unittest tests/test_package_import.py -v`
Expected: PASS。

- [ ] **Step 6: 提交检查点**

```bash
git add pyproject.toml src/a_share_quant/__init__.py tests/test_package_import.py scripts/init_env.py README.md
git commit -m "build: add importable quant research package"
```

### Task 2: 实现 Data 数据读取与校验

**Files:**
- Create: `src/a_share_quant/data.py`
- Create: `tests/test_data.py`

**Interfaces:**
- Consumes: `path: str | Path` 或含 `date, code, open, close, can_trade` 的 DataFrame
- Produces: `validate_daily_data(data: pd.DataFrame) -> None`；`load_daily_data(path: str | Path) -> pd.DataFrame`

- [ ] **Step 1: 写校验失败测试**

测试缺少字段、空表、重复 `(date, code)`、无法解析日期、非正或缺失 `open/close`、非法 `can_trade` 均抛出包含问题字段的 `ValueError`；同时断言校验函数不修改原表。

- [ ] **Step 2: 运行校验测试确认失败**

Run: `python -m unittest tests/test_data.py -v`
Expected: FAIL，原因是模块或函数不存在。

- [ ] **Step 3: 实现 `validate_daily_data()`**

定义 `REQUIRED_DAILY_COLUMNS = ("date", "code", "open", "close", "can_trade")`。校验业务键、类型可转换性、正价格和布尔交易标记；错误信息包含字段名或重复键。

- [ ] **Step 4: 写 CSV 加载测试**

用临时 CSV 断言代码 `000001` 保留前导零，结果按 `code, date` 稳定排序，日期为 Pandas 日期类型，价格为数值，`can_trade` 为布尔值。

- [ ] **Step 5: 实现 `load_daily_data()` 并运行测试**

读取时固定 `code` 为字符串，复制并标准化字段，然后调用校验函数并返回新表。

Run: `python -m unittest tests/test_data.py -v`
Expected: PASS。

- [ ] **Step 6: 提交检查点**

```bash
git add src/a_share_quant/data.py tests/test_data.py
git commit -m "feat: add validated daily data loader"
```

### Task 3: 实现 Factor 与 Signal

**Files:**
- Create: `src/a_share_quant/factor.py`
- Create: `src/a_share_quant/signal.py`
- Create: `tests/test_factor.py`
- Create: `tests/test_signal.py`

**Interfaces:**
- Consumes: Task 2 行情表；因子表列 `date, code, factor_value`
- Produces: `calculate_momentum(data: pd.DataFrame, window: int = 20) -> pd.DataFrame`；`generate_top_n_targets(factors: pd.DataFrame, top_n: int = 2) -> pd.DataFrame`

- [ ] **Step 1: 写动量测试**

断言每只股票独立排序计算；20 日窗口第 21 条首次有效；中间 `close` 缺失不会被填补；`window <= 0`、缺列和重复键报错；原表不变。

- [ ] **Step 2: 运行动量测试确认失败并实现**

Run: `python -m unittest tests/test_factor.py -v`
Expected before implementation: FAIL。

使用 `groupby("code")["close"].pct_change(periods=window, fill_method=None)`，只返回 `date, code, factor_value`。

Run: `python -m unittest tests/test_factor.py -v`
Expected after implementation: PASS。

- [ ] **Step 3: 写目标权重测试**

断言每个日期独立选择最高的前 N 名、等权和为 `1`、NaN 因子排除、并列按 `code` 升序、全日无有效因子时不生成记录；`top_n <= 0`、重复键或非法字段报错。

- [ ] **Step 4: 实现 `generate_top_n_targets()` 并验证**

输出列固定为 `signal_date, code, target_weight`，按 `signal_date, code` 排序。

Run: `python -m unittest tests/test_signal.py -v`
Expected: PASS。

- [ ] **Step 5: 提交检查点**

```bash
git add src/a_share_quant/factor.py src/a_share_quant/signal.py tests/test_factor.py tests/test_signal.py
git commit -m "feat: add momentum factor and target signals"
```

### Task 4: 实现 Portfolio 状态与成交更新

**Files:**
- Create: `src/a_share_quant/portfolio.py`
- Create: `tests/test_portfolio.py`

**Interfaces:**
- Consumes: 目标表、执行价格表和成交表
- Produces: `PortfolioState(cash: float, positions: pd.DataFrame)`；`build_orders(state: PortfolioState, targets: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame`；`apply_fills(state: PortfolioState, fills: pd.DataFrame) -> PortfolioState`

- [ ] **Step 1: 写账户状态与成交测试**

断言买入减少现金并增加 `quantity`，卖出增加现金并减少数量，佣金和印花税方向正确，未成交记录不改变账户，输入状态和 DataFrame 不被原地修改，卖出不得超过持仓。

- [ ] **Step 2: 运行测试确认失败并实现 `PortfolioState`、`apply_fills()`**

成交表固定列：`code, side, quantity, fill_price, commission, stamp_tax, filled`。持仓表固定列：`code, quantity, sellable_quantity`。

Run: `python -m unittest tests/test_portfolio.py -v`
Expected: PASS。

- [ ] **Step 3: 写订单生成测试**

断言根据账户总资产和目标权重得到买卖方向及目标差额；退出目标名单产生卖单；已满足目标不产生订单；目标权重为负或合计超过 `1` 报错。

- [ ] **Step 4: 实现 `build_orders()` 并验证**

订单表固定列：`code, side, order_value, reference_price`。第一版允许小数股数，避免引入尚未定义的整手规则。

Run: `python -m unittest tests/test_portfolio.py -v`
Expected: PASS。

- [ ] **Step 5: 提交检查点**

```bash
git add src/a_share_quant/portfolio.py tests/test_portfolio.py
git commit -m "feat: add portfolio state and fill handling"
```

### Task 5: 实现 Backtest 时间循环与成本

**Files:**
- Create: `src/a_share_quant/backtest.py`
- Create: `tests/test_backtest.py`

**Interfaces:**
- Consumes: Task 2 行情表、Task 3 目标表、Task 4 Portfolio 接口
- Produces: `CostConfig`；`BacktestResult(equity, positions, trades)`；`run_backtest(market_data, targets, initial_cash, cost_config) -> BacktestResult`

- [ ] **Step 1: 写时序和不可交易测试**

断言 `signal_date` 当日不成交、严格下一交易日才尝试；`can_trade=False` 时记录未成交且实际持仓不变；下一次新目标到来前不重复下单；没有有效目标的日期不调仓。

- [ ] **Step 2: 运行测试确认失败并建立时间循环**

Run: `python -m unittest tests/test_backtest.py -v`
Expected before implementation: FAIL。

实现按日期排序推进、下一交易日映射、订单生成、成交状态记录和每日收盘估值。

- [ ] **Step 3: 写费用、滑点和现金约束测试**

固定案例验证买入成交价 `open * (1 + slippage_rate)`、卖出成交价 `open * (1 - slippage_rate)`；佣金取比例金额与最低佣金较大者；印花税只对卖出收取；费用造成现金不足时缩减买入数量且现金不为负；当日新买数量不进入 `sellable_quantity`，下一交易日才可卖。

- [ ] **Step 4: 实现成本与 `BacktestResult` 并验证**

`CostConfig` 默认值使用教学参数：佣金率 `0.0003`、最低佣金 `5.0`、卖出印花税率 `0.0005`、滑点率 `0.001`。交易表保留信号日期、执行日期、状态和未成交原因；每日持仓表记录数量、可卖数量、市值和实际权重，每日净值表记录现金、持仓市值、总资产和标准化净值。

Run: `python -m unittest tests/test_backtest.py -v`
Expected: PASS。

- [ ] **Step 5: 提交检查点**

```bash
git add src/a_share_quant/backtest.py tests/test_backtest.py
git commit -m "feat: add timed backtest execution"
```

### Task 6: 实现 Metrics 与端到端研究链路

**Files:**
- Create: `src/a_share_quant/metrics.py`
- Create: `tests/test_metrics.py`
- Create: `tests/test_research_pipeline.py`

**Interfaces:**
- Consumes: Task 5 `BacktestResult`
- Produces: `calculate_metrics(backtest_result: BacktestResult) -> dict[str, float]`

- [ ] **Step 1: 写累计收益与最大回撤测试**

用净值 `1.00, 1.20, 0.90, 1.10` 断言累计收益 `0.10`、最大回撤 `-0.25`；空净值表、重复日期、非正净值报错；输入结果不变。

- [ ] **Step 2: 实现 `calculate_metrics()` 并验证**

先按日期排序，用首尾净值计算累计收益，用 `cummax()` 计算带符号最大回撤。

Run: `python -m unittest tests/test_metrics.py -v`
Expected: PASS。

- [ ] **Step 3: 写端到端测试**

构造至少两只股票、超过 21 个交易日的虚构行情，依次调用 Data 校验、20 日动量、前一名目标、Backtest 和 Metrics；断言首个目标在第 21 个价格后产生、成交日期晚于信号日期、交易/持仓/净值非空、重复运行结果完全一致。

- [ ] **Step 4: 运行端到端及全量回归**

Run: `python -m unittest tests/test_research_pipeline.py -v`
Expected: PASS。

Run: `python -m unittest discover -s tests -v`
Expected: 现有测试和新增测试全部 PASS。

- [ ] **Step 5: 提交检查点**

```bash
git add src/a_share_quant/metrics.py tests/test_metrics.py tests/test_research_pipeline.py
git commit -m "feat: complete modular research pipeline"
```

### Task 7: 补充使用说明和学习记录

**Files:**
- Modify: `README.md`
- Modify: `docs/learning-notes.md`
- Modify: `docs/progress.md`

**Interfaces:**
- Consumes: 已通过测试的六模块公开接口
- Produces: 与实际代码一致的目录说明、最小研究流程示例和最终学习状态

- [ ] **Step 1: 更新 README**

说明六模块职责、`src` 安装方式和最小导入示例；不添加真实券商或真实交易说明。

- [ ] **Step 2: 更新学习文档**

在 `learning-notes.md` 记录新出现的 `pyproject.toml`、可编辑安装、`dataclass` 和数据契约用法；在 `progress.md` 只记录实际通过的测试和用户已确认的理解。

- [ ] **Step 3: 最终验证**

Run: `python -m unittest discover -s tests -v`
Expected: 全部 PASS。

Run: `git diff --check`
Expected: 无输出，退出码为 0。

- [ ] **Step 4: 提交检查点**

```bash
git add README.md docs/learning-notes.md docs/progress.md
git commit -m "docs: document modular research workflow"
```
