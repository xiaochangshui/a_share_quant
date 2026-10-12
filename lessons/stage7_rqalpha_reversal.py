"""第七阶段：用 RQAlpha 学习 5 日短期反转。

本例使用固定的小型股票池学习因子方向，不用于评价因子的真实有效性。
T 日盘前只能读取到 T-1 日及更早的完整日线；目标在 T 日集合竞价阶段执行。
"""

from pathlib import Path
from typing import Mapping

import numpy as np
from rqalpha import run_func
from rqalpha.apis import (
    history_bars,
    logger,
    order_target_portfolio_smart,
    update_universe,
)


UNIVERSE = (
    "000001.XSHE",
    "600000.XSHG",
    "600036.XSHG",
    "600519.XSHG",
    "601318.XSHG",
)


def calculate_reversal_scores(
    close_histories: Mapping[str, np.ndarray],
    window: int = 5,
) -> dict[str, float]:
    """把过去 window 个交易日的收益取相反数，跌幅越大得分越高。"""
    if window <= 0:
        raise ValueError("window 必须是正整数")

    scores: dict[str, float] = {}
    required_count = window + 1
    for order_book_id, values in close_histories.items():
        closes = np.asarray(values, dtype=float)
        if len(closes) != required_count or not np.isfinite(closes).all():
            continue
        if closes[0] <= 0:
            continue
        scores[order_book_id] = float(1 - closes[-1] / closes[0])
    return scores


def select_target_weights(
    scores: Mapping[str, float],
    top_n: int = 2,
    investable_weight: float = 0.95,
) -> dict[str, float]:
    """按反转得分降序、代码升序选择股票，并分配等权目标。"""
    if top_n <= 0:
        raise ValueError("top_n 必须是正整数")
    if not 0 < investable_weight <= 1:
        raise ValueError("investable_weight 必须大于 0 且不超过 1")

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    selected = [order_book_id for order_book_id, _ in ranked[:top_n]]
    if not selected:
        return {}
    weight = investable_weight / len(selected)
    return {order_book_id: weight for order_book_id in selected}


def init(context) -> None:
    """设置不会随交易日改变的研究参数。"""
    context.stock_pool = list(UNIVERSE)
    context.window = 5
    context.top_n = 2
    context.investable_weight = 0.95
    context.rebalance_interval = 5
    context.trading_day_count = 0
    context.rebalance_today = False
    context.target_weights = {}
    update_universe(context.stock_pool)


def before_trading(context) -> None:
    """盘前使用截至上一交易日的收盘价计算反转目标。"""
    context.rebalance_today = (
        context.trading_day_count % context.rebalance_interval == 0
    )
    context.trading_day_count += 1
    if not context.rebalance_today:
        return

    histories = {
        order_book_id: history_bars(
            order_book_id,
            context.window + 1,
            "1d",
            "close",
            skip_suspended=False,
            include_now=False,
            adjust_type="pre",
        )
        for order_book_id in context.stock_pool
    }
    scores = calculate_reversal_scores(histories, context.window)
    context.target_weights = select_target_weights(
        scores,
        top_n=context.top_n,
        investable_weight=context.investable_weight,
    )
    logger.info(
        "上一交易日收盘反转因子生成目标：{}".format(context.target_weights)
    )


def open_auction(context, bar_dict) -> None:
    """在调仓日集合竞价阶段尝试把实际组合调整到目标权重。"""
    if not context.rebalance_today:
        return
    context.latest_order_results = order_target_portfolio_smart(
        context.target_weights
    )


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    result_dir = root / "result" / "stage7_rqalpha_reversal"
    result_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "base": {
            "data_bundle_path": str(root / "data" / "rqalpha_bundle" / "bundle"),
            "start_date": "2024-01-02",
            "end_date": "2024-06-28",
            "frequency": "1d",
            "accounts": {"stock": 1_000_000},
            "capital_gain_tax_rate": 0,
        },
        "extra": {"log_level": "info"},
        "mod": {
            "sys_accounts": {"stock_t1": True},
            "sys_simulation": {
                "slippage_model": "PriceRatioSlippage",
                "slippage": 0.001,
            },
            "sys_transaction_cost": {
                "stock_min_commission": 5,
                "pit_tax": True,
            },
            "sys_analyser": {
                "enabled": True,
                "strategy_name": "5日短期反转教学策略",
                "benchmark": "000300.XSHG",
                "output_file": str(result_dir / "result.pkl"),
                "report_save_path": str(result_dir / "report"),
            },
        },
    }
    run_func(
        init=init,
        before_trading=before_trading,
        open_auction=open_auction,
        config=config,
    )


if __name__ == "__main__":
    main()
