"""Performance metrics calculated from immutable backtest outputs."""

import pandas as pd
from .backtest import BacktestResult


def calculate_metrics(backtest_result: BacktestResult) -> dict[str, float]:
    """Calculate cumulative return and signed maximum drawdown."""
    if backtest_result.equity.empty:
        raise ValueError("净值表为空")
    required = {"date", "net_value"}
    if not required.issubset(backtest_result.equity):
        raise ValueError("净值表缺少 date 或 net_value")
    equity = backtest_result.equity.loc[:, ["date", "net_value"]].copy()
    equity["date"] = pd.to_datetime(equity["date"], errors="coerce")
    equity["net_value"] = pd.to_numeric(equity["net_value"], errors="coerce")
    if equity["date"].isna().any() or equity["date"].duplicated().any():
        raise ValueError("净值日期无效或重复")
    if equity["net_value"].isna().any() or equity["net_value"].le(0).any():
        raise ValueError("net_value 必须是有效正数")
    equity = equity.sort_values("date", kind="stable").reset_index(drop=True)
    running_peak = equity["net_value"].cummax()
    drawdown = equity["net_value"] / running_peak - 1
    return {
        "cumulative_return": float(equity["net_value"].iloc[-1] / equity["net_value"].iloc[0] - 1),
        "max_drawdown": float(drawdown.min()),
    }
