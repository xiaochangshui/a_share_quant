"""第七阶段：从 RQAlpha 实际成交复算反转策略报告的换手率。

策略换手率描述组合交易强度，和单只股票的成交量换手率不是同一指标。
本例仅复核固定五只示例股票的回测报告，不代表宽基指数策略。
"""

from pathlib import Path

import pandas as pd


def calculate_turnover(
    trades: pd.DataFrame, portfolio: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, float]]:
    """按 RQAlpha 6.4.0 分析器口径复算报告的三项换手指标。"""
    account = portfolio.copy()
    account["date"] = pd.to_datetime(account["date"])
    account["market_value"] = pd.to_numeric(account["market_value"])
    if account["date"].duplicated().any() or (account["market_value"] <= 0).any():
        raise ValueError("账户日期必须唯一，且每日股票市值必须为正")
    account = account.sort_values("date", kind="stable").reset_index(drop=True)

    filled = trades.copy()
    filled["date"] = pd.to_datetime(filled["datetime"]).dt.normalize()
    filled["last_quantity"] = pd.to_numeric(filled["last_quantity"])
    filled["last_price"] = pd.to_numeric(filled["last_price"])
    if not filled["side"].isin(["BUY", "SELL"]).all():
        raise ValueError("成交方向只能是 BUY 或 SELL")
    if (filled["last_quantity"] <= 0).any() or (filled["last_price"] <= 0).any():
        raise ValueError("成交数量和价格必须为正")
    filled["notional"] = filled["last_quantity"] * filled["last_price"]

    by_side = (
        filled.groupby(["date", "side"])["notional"]
        .sum()
        .unstack(fill_value=0)
        .rename(columns={"BUY": "buy_value", "SELL": "sell_value"})
    )
    for column in ("buy_value", "sell_value"):
        if column not in by_side:
            by_side[column] = 0.0
    daily = account[["date", "market_value"]].join(by_side, on="date")
    daily[["buy_value", "sell_value"]] = daily[
        ["buy_value", "sell_value"]
    ].fillna(0.0)
    daily["traded_value"] = daily["buy_value"] + daily["sell_value"]
    daily["daily_turnover"] = daily["traded_value"] / (
        2 * daily["market_value"]
    )

    mean_market_value = float(daily["market_value"].mean())
    turnover = float(daily["traded_value"].sum() / (2 * mean_market_value))
    summary = {
        "total_traded_value": float(daily["traded_value"].sum()),
        "mean_market_value": mean_market_value,
        "turnover": turnover,
        "avg_daily_turnover": float(daily["daily_turnover"].mean()),
        "annualized_twoside_turnover": float(
            turnover * 2 * 252 / len(daily)
        ),
    }
    return daily, summary


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    report = root / "result/stage7_rqalpha_reversal/report"
    output = root / "result/stage7_reversal_turnover"
    output.mkdir(parents=True, exist_ok=True)
    trades = pd.read_csv(report / "trades.csv")
    portfolio = pd.read_csv(report / "portfolio.csv")
    daily, summary = calculate_turnover(trades, portfolio)
    daily.to_csv(output / "daily_turnover.csv", index=False)
    pd.DataFrame([summary]).to_csv(output / "summary.csv", index=False)
    print("固定五只示例股票的反转回测换手率：")
    print(pd.Series(summary).to_string())


if __name__ == "__main__":
    main()
