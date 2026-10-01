"""Loading and validation for daily market data."""

from pathlib import Path
import pandas as pd

REQUIRED_DAILY_COLUMNS = ("date", "code", "open", "close", "can_trade")


def _parse_trade_flag(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value in (1, "1", "true", "True", "TRUE"):
        return True
    if value in (0, "0", "false", "False", "FALSE"):
        return False
    raise ValueError(f"can_trade 包含无法识别的值：{value!r}")


def _normalize(data: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_DAILY_COLUMNS if column not in data]
    if missing:
        raise ValueError("缺少必要字段：" + "、".join(missing))
    if data.empty:
        raise ValueError("日线数据为空")
    result = data.loc[:, REQUIRED_DAILY_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result["code"] = result["code"].astype("string")
    for column in ("open", "close"):
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result["can_trade"] = result["can_trade"].map(_parse_trade_flag).astype(bool)
    return result


def validate_daily_data(data: pd.DataFrame) -> None:
    """Validate the daily-data contract without mutating the input."""
    result = _normalize(data)
    if result["date"].isna().any():
        raise ValueError("date 包含无法解析或缺失的日期")
    if result["code"].isna().any() or result["code"].str.strip().eq("").any():
        raise ValueError("code 包含缺失或空值")
    for column in ("open", "close"):
        if result[column].isna().any() or result[column].le(0).any():
            raise ValueError(f"{column} 必须是有效正数")
    duplicated = result.duplicated(["date", "code"], keep=False)
    if duplicated.any():
        keys = result.loc[duplicated, ["date", "code"]].astype(str).to_dict("records")
        raise ValueError(f"date、code 存在重复记录：{keys}")


def load_daily_data(path: str | Path) -> pd.DataFrame:
    """Load a CSV, normalize its contract fields, validate, and sort it."""
    raw = pd.read_csv(path, dtype={"code": "string"})
    result = _normalize(raw)
    validate_daily_data(result)
    return result.sort_values(["code", "date"], kind="stable").reset_index(drop=True)
