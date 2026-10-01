"""第五阶段：用单日截面的对数市值回归残差调整因子。

示例数据完全虚构，只用于学习市值中性化方法。
"""

from pathlib import Path

import numpy as np
import pandas as pd


def neutralize_by_market_cap(
    data: pd.DataFrame,
    factor_column: str,
    market_cap_column: str = "market_cap",
) -> pd.DataFrame:
    """按日期回归因子对对数市值，并以残差作为中性化因子。"""
    result = data.copy()
    result["date"] = pd.to_datetime(result["date"])
    factor = pd.to_numeric(result[factor_column], errors="coerce")
    market_cap = pd.to_numeric(result[market_cap_column], errors="coerce")

    log_market_cap = pd.Series(np.nan, index=result.index, dtype=float)
    positive_market_cap = market_cap.gt(0)
    log_market_cap.loc[positive_market_cap] = np.log(
        market_cap.loc[positive_market_cap]
    )

    predicted = pd.Series(np.nan, index=result.index, dtype=float)
    residual = pd.Series(np.nan, index=result.index, dtype=float)
    for indices in result.groupby("date", sort=False).groups.values():
        valid = factor.loc[indices].notna() & log_market_cap.loc[indices].notna()
        valid_indices = valid.index[valid]
        if len(valid_indices) < 2:
            continue

        x = log_market_cap.loc[valid_indices]
        y = factor.loc[valid_indices]
        x_deviation = x - x.mean()
        denominator = (x_deviation**2).sum()
        if denominator == 0:
            continue

        slope = (x_deviation * (y - y.mean())).sum() / denominator
        intercept = y.mean() - slope * x.mean()
        predicted.loc[valid_indices] = intercept + slope * x
        residual.loc[valid_indices] = y - predicted.loc[valid_indices]

    result[f"log_{market_cap_column}"] = log_market_cap
    result[f"{factor_column}_size_predicted"] = predicted
    result[f"{factor_column}_size_neutral"] = residual
    return result


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    log_caps = [1.0, 2.0, 3.0]
    sample = pd.DataFrame(
        {
            "date": ["2026-01-05"] * 3 + ["2026-01-06"] * 4,
            "code": ["A", "B", "C", "A", "B", "C", "D"],
            "market_cap": np.exp(log_caps).tolist()
            + np.exp(log_caps).tolist()
            + [0.0],
            "factor": [3.0, 5.0, 7.0, 10.0, 8.0, 7.0, 4.0],
        }
    )

    result = neutralize_by_market_cap(sample, factor_column="factor")
    print("按日期计算的市值回归预测值与残差：")
    print(result.to_string(index=False))

    output_path = root / "result/stage5_market_cap_neutralization.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, date_format="%Y-%m-%d")
    print("\n结果已保存：", output_path)


if __name__ == "__main__":
    main()
