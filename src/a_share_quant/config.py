"""JSON configuration for repeatable research runs."""

from dataclasses import dataclass
import json
from pathlib import Path

from .backtest import CostConfig

CONFIG_FIELDS = {
    "data_path", "output_dir", "momentum_window", "top_n", "initial_cash", "costs"
}
COST_FIELDS = {
    "commission_rate", "minimum_commission", "stamp_tax_rate", "slippage_rate"
}


@dataclass(frozen=True)
class ResearchConfig:
    data_path: Path
    output_dir: Path
    momentum_window: int
    top_n: int
    initial_cash: float
    costs: CostConfig

    def as_dict(self) -> dict[str, object]:
        return {
            "data_path": str(self.data_path),
            "output_dir": str(self.output_dir),
            "momentum_window": self.momentum_window,
            "top_n": self.top_n,
            "initial_cash": self.initial_cash,
            "costs": {
                "commission_rate": self.costs.commission_rate,
                "minimum_commission": self.costs.minimum_commission,
                "stamp_tax_rate": self.costs.stamp_tax_rate,
                "slippage_rate": self.costs.slippage_rate,
            },
        }


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} 必须是正整数")
    return value


def load_research_config(path: str | Path) -> ResearchConfig:
    """Load and validate JSON, resolving paths from the config directory."""
    config_path = Path(path).expanduser().resolve()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"无法读取 JSON 配置：{config_path}") from error
    if not isinstance(payload, dict):
        raise ValueError("配置根节点必须是 JSON 对象")
    missing = sorted(CONFIG_FIELDS - payload.keys())
    unknown = sorted(payload.keys() - CONFIG_FIELDS)
    if missing:
        raise ValueError("缺少配置字段：" + "、".join(missing))
    if unknown:
        raise ValueError("未知配置字段：" + "、".join(unknown))
    if not isinstance(payload["costs"], dict):
        raise ValueError("costs 必须是 JSON 对象")
    missing_costs = sorted(COST_FIELDS - payload["costs"].keys())
    unknown_costs = sorted(payload["costs"].keys() - COST_FIELDS)
    if missing_costs:
        raise ValueError("costs 缺少字段：" + "、".join(missing_costs))
    if unknown_costs:
        raise ValueError("costs 未知字段：" + "、".join(unknown_costs))
    try:
        initial_cash = float(payload["initial_cash"])
        costs = CostConfig(**{name: float(payload["costs"][name]) for name in COST_FIELDS})
    except (TypeError, ValueError) as error:
        raise ValueError("initial_cash 或 costs 包含非数值") from error
    if initial_cash <= 0:
        raise ValueError("initial_cash 必须为正数")
    base = config_path.parent
    return ResearchConfig(
        data_path=(base / str(payload["data_path"])).resolve(),
        output_dir=(base / str(payload["output_dir"])).resolve(),
        momentum_window=_positive_integer(payload["momentum_window"], "momentum_window"),
        top_n=_positive_integer(payload["top_n"], "top_n"),
        initial_cash=initial_cash,
        costs=costs,
    )
