import unittest
import pandas as pd
from a_share_quant.backtest import CostConfig, run_backtest


class BacktestTest(unittest.TestCase):
    def test_executes_after_signal_and_keeps_blocked_trade_unfilled(self):
        market = pd.DataFrame({
            "date": pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"] * 2),
            "code": ["A"] * 3 + ["B"] * 3,
            "open": [10, 10, 10, 20, 20, 20], "close": [10, 11, 12, 20, 20, 20],
            "can_trade": [True, True, True, True, False, True],
        })
        targets = pd.DataFrame({"signal_date": pd.to_datetime(["2026-01-02", "2026-01-02"]), "code": ["A", "B"], "target_weight": [0.5, 0.5]})
        result = run_backtest(market, targets, 10000, CostConfig(0, 0, 0, 0))
        trades = result.trades.set_index("code")
        self.assertEqual(trades.loc["A", "execution_date"], pd.Timestamp("2026-01-05"))
        self.assertTrue(trades.loc["A", "filled"])
        self.assertFalse(trades.loc["B", "filled"])
        self.assertEqual(trades.loc["B", "reason"], "cannot_trade")

    def test_applies_slippage_commission_and_t_plus_one(self):
        market = pd.DataFrame({
            "date": pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"]), "code": ["A"] * 3,
            "open": [10, 10, 10], "close": [10, 10, 10], "can_trade": [True] * 3,
        })
        targets = pd.DataFrame({"signal_date": [pd.Timestamp("2026-01-02")], "code": ["A"], "target_weight": [1.0]})
        result = run_backtest(market, targets, 10000, CostConfig(0.0003, 5, 0.0005, 0.001))
        trade = result.trades.iloc[0]
        self.assertAlmostEqual(trade["fill_price"], 10.01)
        self.assertGreaterEqual(trade["commission"], 5)
        jan5 = result.positions[result.positions["date"] == pd.Timestamp("2026-01-05")].iloc[0]
        jan6 = result.positions[result.positions["date"] == pd.Timestamp("2026-01-06")].iloc[0]
        self.assertEqual(jan5["sellable_quantity"], 0)
        self.assertEqual(jan6["sellable_quantity"], jan6["quantity"])
        self.assertGreaterEqual(result.equity["cash"].min(), 0)


if __name__ == "__main__":
    unittest.main()
