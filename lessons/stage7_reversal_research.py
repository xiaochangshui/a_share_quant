"""第七阶段：在固定五只示例股票上检查短期反转的排序表现。

使用本地 RQAlpha bundle 行情，不声称结果代表任何宽基指数股票池。
每日因子在收盘后才确定；未来五日收益仅作为事后检验标签。
"""

from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from lessons.stage3_ic import calculate_daily_ic
from lessons.stage3_quintile_analysis import (
    assign_quintiles,
    calculate_quintile_returns,
)
from lessons.stage7_rqalpha_reversal import UNIVERSE


def adjusted_closes(
    raw_close: np.ndarray,
    bar_dates: np.ndarray,
    factor_dates: np.ndarray,
    factors: np.ndarray,
) -> np.ndarray:
    """按 bundle 的累计复权因子把各日收盘价放到同一股数口径。"""
    positions = np.searchsorted(factor_dates, bar_dates, side="right") - 1
    if (positions < 0).any():
        raise ValueError("复权因子缺少行情起始日期")
    return np.asarray(raw_close, dtype=float) * np.asarray(factors)[positions]


def prepare_reversal_research(data: pd.DataFrame) -> pd.DataFrame:
    """按股票计算过去五日反转和随后五日收益。"""
    window = 5
    result = data.copy()
    result["date"] = pd.to_datetime(result["date"])
    result["adjusted_close"] = pd.to_numeric(
        result["adjusted_close"], errors="coerce"
    )
    result.loc[result["adjusted_close"] <= 0, "adjusted_close"] = np.nan
    if result.duplicated(["date", "code"]).any():
        raise ValueError("同一交易日和股票代码不能有重复行情")
    result = result.sort_values(["code", "date"], kind="stable").reset_index(
        drop=True
    )

    close_by_stock = result.groupby("code", sort=False)["adjusted_close"]
    previous_close = close_by_stock.shift(window)
    future_close = close_by_stock.shift(-window)
    past_count = close_by_stock.transform(
        lambda closes: closes.rolling(window + 1, min_periods=window + 1).count()
    )
    future_count = close_by_stock.transform(
        lambda closes: closes.iloc[::-1]
        .rolling(window + 1, min_periods=window + 1)
        .count()
        .iloc[::-1]
    )
    result["reversal_5d"] = (1 - result["adjusted_close"] / previous_close).where(
        past_count == window + 1
    )
    result["future_return_5d"] = (
        future_close / result["adjusted_close"] - 1
    ).where(future_count == window + 1)
    return result


def evaluate_reversal(
    prepared: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """先按得分五分组，再分别计算每日 IC 和各组未来收益。"""
    grouped = assign_quintiles(prepared, factor_column="reversal_5d")
    daily_ic = calculate_daily_ic(grouped, factor_column="reversal_5d")
    group_returns = calculate_quintile_returns(grouped)
    return grouped, daily_ic, group_returns


def load_bundle_prices(
    bundle: Path, start_date: str, end_date: str
) -> pd.DataFrame:
    """读取五只示例股票，并对齐本地交易日历；不修改数据包。"""
    calendar = np.load(bundle / "trading_dates.npy")
    start_int = int(start_date.replace("-", ""))
    end_int = int(end_date.replace("-", ""))
    # 保留研究起点之前的交易日，供第一个研究日计算过去五日得分。
    research_start = max(0, np.searchsorted(calendar, start_int) - 5)
    selected_dates = calendar[research_start : np.searchsorted(calendar, end_int, side="right")]
    dates = pd.to_datetime(selected_dates.astype(str), format="%Y%m%d")

    rows = []
    with h5py.File(bundle / "stocks.h5") as bars_file, h5py.File(
        bundle / "ex_cum_factor.h5"
    ) as factors_file:
        for code in UNIVERSE:
            bars = bars_file[code][:]
            ex_factors = factors_file[code][:]
            adjusted = adjusted_closes(
                bars["close"],
                bars["datetime"],
                ex_factors["start_date"],
                ex_factors["ex_cum_factor"],
            )
            stock = pd.DataFrame(
                {
                    "date": pd.to_datetime(
                        (bars["datetime"] // 1_000_000).astype(str),
                        format="%Y%m%d",
                    ),
                    "adjusted_close": adjusted,
                }
            ).set_index("date")
            stock = stock.reindex(dates).rename_axis("date").reset_index()
            stock["code"] = code
            rows.append(stock)
    return pd.concat(rows, ignore_index=True)


def summarize_reversal(
    daily_ic: pd.DataFrame, group_returns: pd.DataFrame
) -> pd.DataFrame:
    """按自然年等权汇总每日 Rank IC 与高低分组的未来收益差。"""
    ic = daily_ic.copy()
    ic["year"] = pd.to_datetime(ic["date"]).dt.year
    ic_summary = ic.groupby("year").agg(
        mean_rank_ic=("rank_ic", "mean"),
        valid_ic_dates=("rank_ic", "count"),
        positive_ic_dates=("rank_ic", lambda x: x.gt(0).sum()),
    )
    ic_summary["positive_ic_share"] = (
        ic_summary["positive_ic_dates"] / ic_summary["valid_ic_dates"]
    )

    groups = group_returns.pivot(
        index="date", columns="quintile", values="mean_future_return"
    )
    groups["g5_minus_g1"] = groups["G5"] - groups["G1"]
    groups["year"] = pd.to_datetime(groups.index).year
    group_summary = groups.groupby("year").agg(
        mean_g1_future_return=("G1", "mean"),
        mean_g5_future_return=("G5", "mean"),
        mean_g5_minus_g1=("g5_minus_g1", "mean"),
        valid_spread_dates=("g5_minus_g1", "count"),
    )
    return ic_summary.join(group_summary).reset_index()


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    bundle = root / "data/rqalpha_bundle/bundle"
    output = root / "result/stage7_reversal_research"
    output.mkdir(parents=True, exist_ok=True)
    prices = load_bundle_prices(bundle, "2024-01-02", "2026-09-30")
    prepared = prepare_reversal_research(prices)
    prepared = prepared.loc[prepared["date"] >= pd.Timestamp("2024-01-02")]
    grouped, daily_ic, group_returns = evaluate_reversal(prepared)
    summary = summarize_reversal(daily_ic, group_returns)

    grouped.to_csv(output / "daily_stock_scores.csv", index=False)
    daily_ic.to_csv(output / "daily_ic.csv", index=False)
    group_returns.to_csv(output / "daily_group_returns.csv", index=False)
    summary.to_csv(output / "yearly_summary.csv", index=False)
    print("固定五只示例股票的年度检查（不代表 A500 或沪深 300）：")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
