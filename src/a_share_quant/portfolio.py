"""Portfolio state, target orders, and fill application."""

from dataclasses import dataclass
import pandas as pd

POSITION_COLUMNS = ["code", "quantity", "sellable_quantity"]


@dataclass
class PortfolioState:
    cash: float
    positions: pd.DataFrame

    def __post_init__(self) -> None:
        self.cash = float(self.cash)
        self.positions = self.positions.loc[:, POSITION_COLUMNS].copy() if not self.positions.empty else pd.DataFrame(columns=POSITION_COLUMNS)
        if self.cash < 0:
            raise ValueError("cash 不能为负")

    @classmethod
    def empty(cls, cash: float) -> "PortfolioState":
        return cls(cash, pd.DataFrame(columns=POSITION_COLUMNS))


def apply_fills(state: PortfolioState, fills: pd.DataFrame) -> PortfolioState:
    """Return a new state after applying successful fills."""
    positions = state.positions.copy()
    cash = float(state.cash)
    for fill in fills.to_dict("records"):
        if not bool(fill["filled"]):
            continue
        code = str(fill["code"])
        side = fill["side"]
        quantity = float(fill["quantity"])
        gross = quantity * float(fill["fill_price"])
        commission = float(fill.get("commission", 0.0))
        stamp_tax = float(fill.get("stamp_tax", 0.0))
        indexed = positions.set_index("code") if not positions.empty else pd.DataFrame(columns=["quantity", "sellable_quantity"])
        current = float(indexed.loc[code, "quantity"]) if code in indexed.index else 0.0
        sellable = float(indexed.loc[code, "sellable_quantity"]) if code in indexed.index else 0.0
        if side == "buy":
            cost = gross + commission + stamp_tax
            if cost > cash + 1e-9:
                raise ValueError("买入成交金额和费用超过可用现金")
            cash -= cost
            current += quantity
        elif side == "sell":
            if quantity > sellable + 1e-9:
                raise ValueError("卖出数量超过可卖数量")
            cash += gross - commission - stamp_tax
            current -= quantity
            sellable -= quantity
        else:
            raise ValueError(f"未知交易方向：{side}")
        positions = positions.loc[positions["code"] != code]
        if current > 1e-12:
            row = pd.DataFrame({"code": [code], "quantity": [current], "sellable_quantity": [sellable]})
            positions = row if positions.empty else pd.concat([positions, row], ignore_index=True)
    return PortfolioState(cash, positions.sort_values("code", kind="stable").reset_index(drop=True))


def build_orders(state: PortfolioState, targets: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Build value-difference orders from current and target holdings."""
    required_targets = {"code", "target_weight"}
    required_prices = {"code", "price"}
    if not required_targets.issubset(targets) or not required_prices.issubset(prices):
        raise ValueError("targets 或 prices 缺少必要字段")
    target = targets.loc[:, ["code", "target_weight"]].copy()
    target["target_weight"] = pd.to_numeric(target["target_weight"], errors="coerce")
    if target["target_weight"].isna().any() or target["target_weight"].lt(0).any() or target["target_weight"].sum() > 1 + 1e-9:
        raise ValueError("目标权重必须非负且合计不超过 1")
    price_map = prices.set_index("code")["price"].astype(float)
    current_values: dict[str, float] = {}
    for row in state.positions.to_dict("records"):
        if row["code"] not in price_map:
            raise ValueError(f"缺少持仓 {row['code']} 的价格")
        current_values[row["code"]] = float(row["quantity"]) * float(price_map[row["code"]])
    equity = state.cash + sum(current_values.values())
    target_map = target.set_index("code")["target_weight"].to_dict()
    rows = []
    for code in sorted(set(current_values) | set(target_map)):
        if code not in price_map:
            raise ValueError(f"缺少目标 {code} 的价格")
        difference = equity * float(target_map.get(code, 0.0)) - current_values.get(code, 0.0)
        if abs(difference) <= 1e-9:
            continue
        rows.append({"code": code, "side": "buy" if difference > 0 else "sell", "order_value": difference, "reference_price": float(price_map[code])})
    return pd.DataFrame(rows, columns=["code", "side", "order_value", "reference_price"])
