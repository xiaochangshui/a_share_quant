# a_share_quant

A 股量化学习项目。

- [完整学习路线](docs/learning-roadmap.md)
- [当前学习进度](docs/progress.md)
- [关键知识与 Python 用法汇总](docs/learning-notes.md)

## 初始化环境（Linux / Windows）

先安装 Python 3.10 或更高版本。首次安装依赖需要联网。
虚拟环境 `.venv` 是本项目独立存放 Python 和第三方工具的目录；
`requirements.txt` 记录需要安装的工具，包括处理表格的 Pandas、绘图的 Matplotlib，
以及获取公开行情数据的 AKShare。

在项目根目录运行以下命令。

Linux：

```bash
python3 scripts/init_env.py
```

Windows（PowerShell 或 cmd）：

```powershell
py -3 scripts/init_env.py
```

如果 Windows 没有 `py` 命令，但 `python --version` 能正常显示版本，使用：

```powershell
python scripts/init_env.py
```

脚本会创建或复用 `.venv`、安装依赖、以可编辑方式安装本项目，并验证 Pandas 和
`a_share_quant` 包能否导入。预期最后输出两者的版本号和 `Environment ready.`，
随后显示激活命令。可编辑安装使 `src/a_share_quant/` 中的代码修改立即在环境中生效；
安装过程复用环境内已有的构建工具，不额外创建联网下载构建依赖的隔离环境。
重复运行会复用现有环境；遇到不完整或来自另一操作系统的 `.venv` 会报错，
请先将该目录改名备份，再重试。脚本不会自动删除已有目录。

脚本通过自己的位置定位项目，因此也可用脚本的绝对路径从其他目录运行。
依赖目前未锁定版本，不同时间首次安装得到的版本可能不同。

## 使用环境

激活环境就是让当前终端的 `python` 命令使用项目的 Python。
初始化脚本不能替父终端完成激活，需要在项目根目录手动运行。

Linux：

```bash
source .venv/bin/activate
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows cmd：

```bat
.venv\Scripts\activate.bat
```

激活后验证：

```bash
python -c "import pandas as pd; print(pd.__version__)"
```

预期输出版本号且没有报错。若 PowerShell 阻止激活脚本，
可以直接使用环境内的 Python，无需修改执行策略：

```powershell
.\.venv\Scripts\python.exe -c "import pandas as pd; print(pd.__version__)"
```

## 模块化研究代码

可复用代码位于 `src/a_share_quant/`：

- `data.py`：读取并检查日线数据；
- `factor.py`：计算 20 日动量等因子；
- `signal.py`：按因子生成前 N 名等权目标；
- `portfolio.py`：生成调整订单并根据成交记录更新账户；
- `backtest.py`：按交易日模拟下一交易日执行、交易成本和 T+1；
- `metrics.py`：计算累计收益和最大回撤。

模块通过字段明确的 DataFrame 交换数据。最小研究流程如下：

```python
from a_share_quant.backtest import CostConfig, run_backtest
from a_share_quant.data import load_daily_data
from a_share_quant.factor import calculate_momentum
from a_share_quant.metrics import calculate_metrics
from a_share_quant.signal import generate_top_n_targets

market = load_daily_data("data/daily.csv")
factors = calculate_momentum(market, window=20)
targets = generate_top_n_targets(factors, top_n=5)
result = run_backtest(market, targets, initial_cash=100_000, cost_config=CostConfig())
metrics = calculate_metrics(result)
```

`result.equity`、`result.positions` 和 `result.trades` 分别保存净值、实际持仓和交易记录。

## 本次验收问题

1. 初始化结束时是否出现 `Environment ready.`？
2. 使用环境内的 Python，是否能打印 Pandas 版本号？
3. 为什么要为项目创建独立的 `.venv`？
