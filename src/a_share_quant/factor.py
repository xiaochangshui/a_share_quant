"""Factor calculations."""

import pandas as pd


def calculate_momentum(data: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Calculate close-to-close momentum independently for each stock."""
    if not isinstance(window, int) or window <= 0:
        raise ValueError("window 必须是正整数")
    required = ["date", "code", "close"]
    missing = [column for column in required if column not in data]
    if missing:
        raise ValueError("缺少必要字段：" + "、".join(missing))
    result = data.loc[:, required].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result["close"] = pd.to_numeric(result["close"], errors="coerce")
    if result["date"].isna().any():
        raise ValueError("date 包含无效值")
    if result.duplicated(["date", "code"]).any():
        raise ValueError("date、code 存在重复记录")
    result = result.sort_values(["code", "date"], kind="stable").reset_index(drop=True)
    result["factor_value"] = result.groupby("code")["close"].pct_change(
        periods=window, fill_method=None
    )
    return result[["date", "code", "factor_value"]]
