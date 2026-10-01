"""A small daily-bar backtest coordinator."""

from dataclasses import dataclass
import pandas as pd

from .data import validate_daily_data
from .portfolio import PortfolioState, apply_fills, build_orders


@dataclass(frozen=True)
class CostConfig:
    commission_rate: float = 0.0003
    minimum_commission: float = 5.0
    stamp_tax_rate: float = 0.0005
    slippage_rate: float = 0.001

    def __post_init__(self) -> None:
        if min(self.commission_rate, self.minimum_commission, self.stamp_tax_rate, self.slippage_rate) < 0:
            raise ValueError("交易成本参数不能为负")


@dataclass
class BacktestResult:
    equity: pd.DataFrame
    positions: pd.DataFrame
    trades: pd.DataFrame


TRADE_COLUMNS = [
    "signal_date", "execution_date", "code", "side", "quantity",
    "reference_price", "fill_price", "gross_amount", "commission",
    "stamp_tax", "filled", "reason",
]


def _commission(gross: float, config: CostConfig) -> float:
    return max(gross * config.commission_rate, config.minimum_commission) if gross > 0 else 0.0


def _affordable_quantity(desired: float, price: float, cash: float, config: CostConfig) -> float:
    def total(quantity: float) -> float:
        gross = quantity * price
        return gross + _commission(gross, config)

    if total(desired) <= cash:
        return desired
    low, high = 0.0, desired
    for _ in range(60):
        middle = (low + high) / 2
        if total(middle) <= cash:
            low = middle
        else:
            high = middle
    return low


def run_backtest(
    market_data: pd.DataFrame,
    targets: pd.DataFrame,
    initial_cash: float,
    cost_config: CostConfig | None = None,
) -> BacktestResult:
    """Execute close-generated targets at the next trading day's open."""
    if initial_cash <= 0:
        raise ValueError("initial_cash 必须为正数")
    config = cost_config or CostConfig()
    market = market_data.copy()
    validate_daily_data(market)
    market["date"] = pd.to_datetime(market["date"])
    market = market.sort_values(["date", "code"], kind="stable").reset_index(drop=True)
    required_targets = ["signal_date", "code", "target_weight"]
    missing = [column for column in required_targets if column not in targets]
    if missing:
        raise ValueError("目标表缺少必要字段：" + "、".join(missing))
    target_data = targets.loc[:, required_targets].copy()
    target_data["signal_date"] = pd.to_datetime(target_data["signal_date"], errors="coerce")
    if target_data["signal_date"].isna().any():
        raise ValueError("signal_date 包含无效值")

    dates = pd.Index(market["date"].drop_duplicates().sort_values())
    due: dict[pd.Timestamp, list[tuple[pd.Timestamp, pd.DataFrame]]] = {}
    for signal_date, same_signal in target_data.groupby("signal_date", sort=True):
        position = dates.searchsorted(signal_date, side="right")
        if position < len(dates):
            due.setdefault(dates[position], []).append((signal_date, same_signal[["code", "target_weight"]]))

    state = PortfolioState.empty(initial_cash)
    equity_rows: list[dict[str, object]] = []
    position_rows: list[dict[str, object]] = []
    trade_rows: list[dict[str, object]] = []
    for date in dates:
        if not state.positions.empty:
            unlocked = state.positions.copy()
            unlocked["sellable_quantity"] = unlocked["quantity"]
            state = PortfolioState(state.cash, unlocked)
        today = market.loc[market["date"] == date].copy()
        open_prices = today[["code", "open"]].rename(columns={"open": "price"})
        trade_flags = today.set_index("code")["can_trade"].to_dict()
        for signal_date, same_signal in due.get(date, []):
            orders = build_orders(state, same_signal, open_prices)
            if not orders.empty:
                orders = orders.assign(priority=orders["side"].map({"sell": 0, "buy": 1})).sort_values(["priority", "code"])
            for order in orders.to_dict("records"):
                code = order["code"]
                side = order["side"]
                reference = float(order["reference_price"])
                fill_price = reference * (1 + config.slippage_rate if side == "buy" else 1 - config.slippage_rate)
                desired = abs(float(order["order_value"])) / fill_price
                reason = ""
                filled = bool(trade_flags.get(code, False))
                quantity = desired
                if not filled:
                    reason = "cannot_trade"
                    quantity = 0.0
                elif side == "sell":
                    held = state.positions.set_index("code") if not state.positions.empty else pd.DataFrame()
                    sellable = float(held.loc[code, "sellable_quantity"]) if code in held.index else 0.0
                    quantity = min(desired, sellable)
                    if quantity <= 1e-12:
                        filled, reason = False, "not_sellable"
                else:
                    quantity = _affordable_quantity(desired, fill_price, state.cash, config)
                    if quantity <= 1e-12:
                        filled, reason = False, "insufficient_cash"
                gross = quantity * fill_price
                commission = _commission(gross, config) if filled else 0.0
                stamp_tax = gross * config.stamp_tax_rate if filled and side == "sell" else 0.0
                trade = {
                    "signal_date": signal_date, "execution_date": date, "code": code,
                    "side": side, "quantity": quantity, "reference_price": reference,
                    "fill_price": fill_price, "gross_amount": gross,
                    "commission": commission, "stamp_tax": stamp_tax,
                    "filled": filled, "reason": reason,
                }
                trade_rows.append(trade)
                state = apply_fills(state, pd.DataFrame([trade]))

        close_map = today.set_index("code")["close"].astype(float)
        position_value = 0.0
        for row in state.positions.to_dict("records"):
            if row["code"] not in close_map:
                raise ValueError(f"缺少持仓 {row['code']} 在 {date.date()} 的收盘价")
            value = float(row["quantity"]) * float(close_map[row["code"]])
            position_value += value
            position_rows.append({
                "date": date, "code": row["code"], "quantity": row["quantity"],
                "sellable_quantity": row["sellable_quantity"], "market_value": value,
            })
        total = state.cash + position_value
        equity_rows.append({"date": date, "cash": state.cash, "position_value": position_value, "total_equity": total, "net_value": total / initial_cash})

    equity = pd.DataFrame(equity_rows)
    positions = pd.DataFrame(position_rows, columns=["date", "code", "quantity", "sellable_quantity", "market_value"])
    if not positions.empty:
        totals = equity.set_index("date")["total_equity"]
        positions["actual_weight"] = positions["market_value"] / positions["date"].map(totals)
    else:
        positions["actual_weight"] = pd.Series(dtype=float)
    trades = pd.DataFrame(trade_rows, columns=TRADE_COLUMNS)
    return BacktestResult(equity, positions, trades)
