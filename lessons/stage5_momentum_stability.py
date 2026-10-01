"""第五阶段：比较多个动量观察窗口并按年份检查 Rank IC 稳定性。

示例价格为虚构的复权价格，只用于学习参数比较方法，不代表真实行情。
"""

from math import sin
from pathlib import Path

import pandas as pd


def prepare_momentum_research(
    data: pd.DataFrame,
    periods: tuple[int, ...] = (5, 20, 60),
    future_periods: int = 5,
) -> pd.DataFrame:
    """按股票计算多个动量窗口和指定期限的未来收益。"""
    result = data.copy()
    result["date"] = pd.to_datetime(result["date"])
    result["adjusted_close"] = pd.to_numeric(result["adjusted_close"])
    result = result.sort_values(["code", "date"], kind="stable").reset_index(
        drop=True
    )

    grouped_close = result.groupby("code")["adjusted_close"]
    for period in periods:
        result[f"momentum_{period}d"] = grouped_close.pct_change(
            periods=period,
            fill_method=None,
        )

    future_close = grouped_close.shift(-future_periods)
    result[f"future_return_{future_periods}d"] = (
        future_close / result["adjusted_close"] - 1
    )
    return result


def calculate_common_sample_rank_ic(
    data: pd.DataFrame,
    periods: tuple[int, ...] = (5, 20, 60),
    future_return_column: str = "future_return_5d",
) -> pd.DataFrame:
    """在每个日期用所有窗口共同有效的股票计算各窗口 Rank IC。"""
    result = data.copy()
    result["date"] = pd.to_datetime(result["date"])
    factor_columns = [f"momentum_{period}d" for period in periods]
    required_columns = factor_columns + [future_return_column]
    common_sample = result.loc[result[required_columns].notna().all(axis=1)]

    rows: list[dict[str, object]] = []
    for date, same_day in common_sample.groupby("date", sort=True):
        future_rank = same_day[future_return_column].rank(method="average")
        for period, factor_column in zip(periods, factor_columns):
            rank_ic = float("nan")
            if (
                len(same_day) >= 2
                and same_day[factor_column].nunique() >= 2
                and same_day[future_return_column].nunique() >= 2
            ):
                factor_rank = same_day[factor_column].rank(method="average")
                rank_ic = factor_rank.corr(future_rank)
            rows.append(
                {
                    "date": date,
                    "period": period,
                    "valid_pair_count": len(same_day),
                    "rank_ic": rank_ic,
                }
            )
    return pd.DataFrame(rows)


def summarize_rank_ic_by_year(daily_ic: pd.DataFrame) -> pd.DataFrame:
    """按动量窗口和自然年汇总有效 Rank IC。"""
    result = daily_ic.copy()
    result["date"] = pd.to_datetime(result["date"])
    result["year"] = result["date"].dt.year
    valid = result.loc[result["rank_ic"].notna()]
    summary = (
        valid.groupby(["period", "year"])
        .agg(
            mean_rank_ic=("rank_ic", "mean"),
            valid_date_count=("rank_ic", "count"),
            positive_ic_ratio=("rank_ic", lambda values: values.gt(0).mean()),
        )
        .reset_index()
    )
    return summary.sort_values(["period", "year"], kind="stable").reset_index(
        drop=True
    )


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    dates = pd.bdate_range("2025-09-01", periods=180)
    price_functions = {
        "A": lambda index: 100 + 0.20 * index + 2 * sin(index / 7),
        "B": lambda index: 100 + 0.12 * index + 3 * sin(index / 11 + 0.5),
        "C": lambda index: 100 + 0.05 * index + 4 * sin(index / 9 + 1),
        "D": lambda index: 100 - 0.02 * index + 3 * sin(index / 13 + 2),
        "E": lambda index: 100 + 0.09 * index + 5 * sin(index / 17 + 3),
    }
    sample = pd.concat(
        [
            pd.DataFrame(
                {
                    "date": dates,
                    "code": code,
                    "adjusted_close": [function(index) for index in range(len(dates))],
                }
            )
            for code, function in price_functions.items()
        ],
        ignore_index=True,
    )

    prepared = prepare_momentum_research(sample)
    daily_ic = calculate_common_sample_rank_ic(prepared)
    yearly_summary = summarize_rank_ic_by_year(daily_ic)

    print("各窗口按年份的 Rank IC 汇总：")
    print(yearly_summary.to_string(index=False))

    detail_output = root / "result/stage5_momentum_windows.csv"
    daily_output = root / "result/stage5_momentum_daily_rank_ic.csv"
    summary_output = root / "result/stage5_momentum_yearly_summary.csv"
    detail_output.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(detail_output, index=False, date_format="%Y-%m-%d")
    daily_ic.to_csv(daily_output, index=False, date_format="%Y-%m-%d")
    yearly_summary.to_csv(summary_output, index=False)
    print("\n结果已保存：", detail_output)
    print("结果已保存：", daily_output)
    print("结果已保存：", summary_output)


if __name__ == "__main__":
    main()
