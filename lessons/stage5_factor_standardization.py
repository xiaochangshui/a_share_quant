"""第五阶段：在同日股票截面内对因子做 Z-score 标准化。

示例数据完全虚构，只用于学习标准化方法，不代表真实股票或行情。
"""

from pathlib import Path

import pandas as pd


def standardize_factors(
    data: pd.DataFrame,
    factor_columns: list[str],
) -> pd.DataFrame:
    """按日期分别计算多个因子的 Z-score，保留原始列和缺失值。"""
    result = data.copy()
    result["date"] = pd.to_datetime(result["date"])

    for factor_column in factor_columns:
        values = pd.to_numeric(result[factor_column], errors="coerce")
        same_date = values.groupby(result["date"])
        daily_mean = same_date.transform("mean")
        daily_std = same_date.transform("std")
        result[f"{factor_column}_zscore"] = (
            values - daily_mean
        ) / daily_std

    return result


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    sample = pd.DataFrame(
        {
            "date": ["2026-01-05"] * 3 + ["2026-01-06"] * 3,
            "code": ["A", "B", "C"] * 2,
            "momentum": [10.0, 20.0, 30.0, 100.0, 200.0, float("nan")],
            "quality": [30.0, 20.0, 10.0, 5.0, 5.0, 5.0],
        }
    )

    result = standardize_factors(
        sample,
        factor_columns=["momentum", "quality"],
    )
    print("按日期分别计算的因子 Z-score：")
    print(result.to_string(index=False))

    output_path = root / "result/stage5_factor_standardization.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, date_format="%Y-%m-%d")
    print("\n结果已保存：", output_path)


if __name__ == "__main__":
    main()
