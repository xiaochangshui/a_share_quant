"""第五阶段：用同日同行业均值调整因子。

示例数据完全虚构，只用于学习行业中性化的直观方法。
"""

from pathlib import Path

import pandas as pd


def neutralize_by_industry_mean(
    data: pd.DataFrame,
    factor_column: str,
    industry_column: str = "industry",
) -> pd.DataFrame:
    """用个股因子减去同日同行业平均因子。"""
    result = data.copy()
    result["date"] = pd.to_datetime(result["date"])
    values = pd.to_numeric(result[factor_column], errors="coerce")
    industry_mean = values.groupby(
        [result["date"], result[industry_column]]
    ).transform("mean")

    result[f"{factor_column}_industry_mean"] = industry_mean
    result[f"{factor_column}_industry_neutral"] = values - industry_mean
    return result


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    sample = pd.DataFrame(
        {
            "date": ["2026-01-05"] * 5 + ["2026-01-06"] * 4,
            "code": ["A", "B", "C", "D", "E", "A", "B", "C", "D"],
            "industry": [
                "科技",
                "科技",
                "银行",
                "银行",
                "单股票行业",
                "科技",
                "科技",
                "银行",
                None,
            ],
            "factor": [3.0, 1.0, 10.0, 8.0, 5.0, 30.0, 10.0, 7.0, 4.0],
        }
    )

    result = neutralize_by_industry_mean(sample, factor_column="factor")
    print("同日同行业均值调整结果：")
    print(result.to_string(index=False))

    output_path = root / "result/stage5_industry_neutralization.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, date_format="%Y-%m-%d")
    print("\n结果已保存：", output_path)


if __name__ == "__main__":
    main()
