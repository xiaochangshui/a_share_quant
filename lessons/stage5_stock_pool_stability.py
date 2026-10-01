"""第五阶段：比较因子在不同历史股票池中的 Rank IC 稳定性。

示例数据和股票池完全虚构，只用于学习比较方法。
"""

from pathlib import Path

import pandas as pd


def calculate_pool_daily_rank_ic(
    research_data: pd.DataFrame,
    membership_data: pd.DataFrame,
    factor_column: str = "factor",
    future_return_column: str = "future_return",
) -> pd.DataFrame:
    """按历史成员资格计算每个股票池的逐日 Rank IC。"""
    research = research_data.copy()
    membership = membership_data.copy()
    research["date"] = pd.to_datetime(research["date"])
    membership["date"] = pd.to_datetime(membership["date"])
    research[factor_column] = pd.to_numeric(
        research[factor_column], errors="coerce"
    )
    research[future_return_column] = pd.to_numeric(
        research[future_return_column], errors="coerce"
    )

    membership = membership[["date", "code", "pool"]].drop_duplicates()
    matched = membership.merge(
        research[["date", "code", factor_column, future_return_column]],
        on=["date", "code"],
        how="inner",
        validate="many_to_one",
    )

    rows: list[dict[str, object]] = []
    for (date, pool), same_pool in matched.groupby(["date", "pool"], sort=True):
        valid = (
            same_pool[[factor_column, future_return_column]].notna().all(axis=1)
        )
        valid_pairs = same_pool.loc[valid]
        rank_ic = float("nan")
        if (
            len(valid_pairs) >= 2
            and valid_pairs[factor_column].nunique() >= 2
            and valid_pairs[future_return_column].nunique() >= 2
        ):
            factor_rank = valid_pairs[factor_column].rank(method="average")
            future_rank = valid_pairs[future_return_column].rank(
                method="average"
            )
            rank_ic = factor_rank.corr(future_rank)

        member_count = len(same_pool)
        valid_pair_count = len(valid_pairs)
        rows.append(
            {
                "date": date,
                "pool": pool,
                "member_count": member_count,
                "valid_pair_count": valid_pair_count,
                "missing_pair_count": member_count - valid_pair_count,
                "rank_ic": rank_ic,
            }
        )

    return pd.DataFrame(rows)


def summarize_pool_rank_ic(daily_ic: pd.DataFrame) -> pd.DataFrame:
    """按股票池汇总 Rank IC 和样本数量。"""
    rows: list[dict[str, object]] = []
    for pool, same_pool in daily_ic.groupby("pool", sort=True):
        valid_ic = same_pool["rank_ic"].dropna()
        rows.append(
            {
                "pool": pool,
                "mean_rank_ic": valid_ic.mean(),
                "valid_date_count": valid_ic.count(),
                "positive_ic_ratio": valid_ic.gt(0).mean(),
                "average_member_count": same_pool["member_count"].mean(),
                "average_valid_stock_count": same_pool[
                    "valid_pair_count"
                ].mean(),
                "average_missing_pair_count": same_pool[
                    "missing_pair_count"
                ].mean(),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    dates = pd.to_datetime(["2026-01-05", "2026-01-06"])
    research = pd.DataFrame(
        {
            "date": dates.repeat(4),
            "code": ["A", "B", "C", "D"] * 2,
            "factor": [1.0, 2.0, 3.0, 4.0] * 2,
            "future_return": [1.0, 2.0, 4.0, 3.0, 4.0, 3.0, 1.0, 2.0],
        }
    )
    print("示例研究数据：")
    print(research)
    membership_rows: list[dict[str, object]] = []
    for date in dates:
        for code in ["A", "B", "C", "D"]:
            membership_rows.append(
                {"date": date, "code": code, "pool": "全市场"}
            )
        for code in ["A", "B"]:
            membership_rows.append(
                {"date": date, "code": code, "pool": "大盘股"}
            )
        for code in ["C", "D"]:
            membership_rows.append(
                {"date": date, "code": code, "pool": "中小盘股"}
            )
    membership = pd.DataFrame(membership_rows)
    print("\n示例股票池成员资格：")
    print(membership)

    daily_ic = calculate_pool_daily_rank_ic(research, membership)
    summary = summarize_pool_rank_ic(daily_ic)
    print("各股票池稳定性汇总：")
    print(summary.to_string(index=False))

    daily_output = root / "result/stage5_stock_pool_daily_rank_ic.csv"
    summary_output = root / "result/stage5_stock_pool_stability_summary.csv"
    daily_output.parent.mkdir(parents=True, exist_ok=True)
    daily_ic.to_csv(daily_output, index=False, date_format="%Y-%m-%d")
    summary.to_csv(summary_output, index=False)
    print("\n结果已保存：", daily_output)
    print("结果已保存：", summary_output)


if __name__ == "__main__":
    main()
