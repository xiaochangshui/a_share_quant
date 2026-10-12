import importlib
import unittest

import pandas as pd


class ReversalTurnoverTest(unittest.TestCase):
    def test_report_turnover_uses_filled_notional_and_mean_stock_value(self):
        module = importlib.import_module("lessons.stage7_reversal_turnover")
        portfolio = pd.DataFrame(
            {
                "date": ["2024-01-02", "2024-01-03"],
                "market_value": [100.0, 200.0],
                "total_value": [150.0, 250.0],
            }
        )
        trades = pd.DataFrame(
            {
                "datetime": ["2024-01-02", "2024-01-03", "2024-01-03"],
                "side": ["BUY", "SELL", "BUY"],
                "last_quantity": [10.0, 4.0, 6.0],
                "last_price": [10.0, 10.0, 10.0],
                "transaction_cost": [9.0, 8.0, 7.0],
            }
        )

        daily, summary = module.calculate_turnover(trades, portfolio)

        self.assertAlmostEqual(summary["turnover"], 2 / 3)
        self.assertAlmostEqual(summary["avg_daily_turnover"], 0.375)
        self.assertAlmostEqual(summary["annualized_twoside_turnover"], 168.0)
        self.assertEqual(daily["traded_value"].tolist(), [100.0, 100.0])
        self.assertEqual(daily["buy_value"].tolist(), [100.0, 60.0])
        self.assertEqual(daily["sell_value"].tolist(), [0.0, 40.0])

    def test_nontrading_day_is_zero_and_does_not_count_rejected_orders(self):
        module = importlib.import_module("lessons.stage7_reversal_turnover")
        portfolio = pd.DataFrame(
            {
                "date": ["2024-01-02", "2024-01-03"],
                "market_value": [100.0, 100.0],
            }
        )
        trades = pd.DataFrame(
            {
                "datetime": ["2024-01-02"],
                "side": ["BUY"],
                "last_quantity": [10.0],
                "last_price": [10.0],
            }
        )

        daily, summary = module.calculate_turnover(trades, portfolio)

        self.assertEqual(daily["traded_value"].tolist(), [100.0, 0.0])
        self.assertEqual(daily["daily_turnover"].tolist(), [0.5, 0.0])
        self.assertAlmostEqual(summary["avg_daily_turnover"], 0.25)


if __name__ == "__main__":
    unittest.main()
