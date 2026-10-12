import importlib
import unittest

import numpy as np
import pandas as pd


class ReversalResearchTest(unittest.TestCase):
    def setUp(self):
        self.module = importlib.import_module("lessons.stage7_reversal_research")

    def test_adjustment_factor_removes_mechanical_price_drop(self):
        raw_close = np.array([10.0, 5.0])
        bar_dates = np.array([20240102000000, 20240103000000])
        factor_dates = np.array([0, 20240103000000])
        factors = np.array([1.0, 2.0])

        adjusted = self.module.adjusted_closes(
            raw_close, bar_dates, factor_dates, factors
        )

        np.testing.assert_allclose(adjusted, [10.0, 10.0])

    def test_reversal_uses_five_past_and_five_future_trading_days(self):
        dates = pd.bdate_range("2024-01-01", periods=12)
        rows = pd.DataFrame(
            {
                "date": dates,
                "code": "A",
                "adjusted_close": [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89],
            }
        )
        rows.loc[3, "adjusted_close"] = np.nan

        prepared = self.module.prepare_reversal_research(rows)
        by_date = prepared.set_index("date")

        self.assertTrue(np.isnan(by_date.loc[dates[5], "reversal_5d"]))
        self.assertAlmostEqual(by_date.loc[dates[9], "reversal_5d"], 1 - 91 / 96)
        self.assertAlmostEqual(
            by_date.loc[dates[5], "future_return_5d"], 90 / 95 - 1
        )
        self.assertTrue(np.isnan(by_date.loc[dates[0], "future_return_5d"]))
        self.assertTrue(np.isnan(by_date.loc[dates[7], "future_return_5d"]))

    def test_groups_are_chosen_before_missing_future_returns_are_removed(self):
        sample = pd.DataFrame(
            {
                "date": ["2024-01-02"] * 5,
                "code": list("ABCDE"),
                "reversal_5d": [1, 2, 3, 4, 5],
                "future_return_5d": [0.01, 0.02, np.nan, 0.04, 0.05],
            }
        )

        _, daily_ic, group_returns = self.module.evaluate_reversal(sample)

        self.assertEqual(daily_ic.iloc[0]["valid_pair_count"], 4)
        self.assertAlmostEqual(daily_ic.iloc[0]["rank_ic"], 1.0)
        middle = group_returns.loc[group_returns["quintile"] == "G3"].iloc[0]
        self.assertEqual(middle["original_count"], 1)
        self.assertEqual(middle["valid_return_count"], 0)
        self.assertEqual(middle["missing_return_count"], 1)


if __name__ == "__main__":
    unittest.main()
