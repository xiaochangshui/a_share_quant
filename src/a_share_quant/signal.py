"""Conversion of factor scores into target weights."""

import pandas as pd


def generate_top_n_targets(factors: pd.DataFrame, top_n: int = 2) -> pd.DataFrame:
    """Select each date's top factor values and assign equal target weights."""
    if not isinstance(top_n, int) or top_n <= 0:
        raise ValueError("top_n 必须是正整数")
    required = ["date", "code", "factor_value"]
    missing = [column for column in required if column not in factors]
    if missing:
        raise ValueError("缺少必要字段：" + "、".join(missing))
    result = factors.loc[:, required].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result["factor_value"] = pd.to_numeric(result["factor_value"], errors="coerce")
    if result["date"].isna().any():
        raise ValueError("date 包含无效值")
    if result.duplicated(["date", "code"]).any():
        raise ValueError("date、code 存在重复记录")
    valid = result.loc[result["factor_value"].notna()].sort_values(
        ["date", "factor_value", "code"], ascending=[True, False, True], kind="stable"
    )
    selected = valid.groupby("date", sort=True, group_keys=False).head(top_n).copy()
    if selected.empty:
        return pd.DataFrame(columns=["signal_date", "code", "target_weight"])
    counts = selected.groupby("date")["code"].transform("size")
    selected["target_weight"] = 1.0 / counts
    selected = selected.rename(columns={"date": "signal_date"})
    return selected[["signal_date", "code", "target_weight"]].sort_values(
        ["signal_date", "code"], kind="stable"
    ).reset_index(drop=True)
