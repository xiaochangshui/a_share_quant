import importlib
import unittest

import pandas as pd


def load_functions():
    try:
        module = importlib.import_module("lessons.stage5_momentum_stability")
    except ModuleNotFoundError:
        return None, None, None
    return (
        module.prepare_momentum_research,
        module.calculate_common_sample_rank_ic,
        module.summarize_rank_ic_by_year,
    )


class MomentumStabilityTest(unittest.TestCase):
    def test_calculates_multiple_windows_and_future_return_within_each_stock(self):
        prepare, _, _ = load_functions()
        self.assertIsNotNone(prepare, "动量稳定性教学脚本尚未实现")
        dates = pd.bdate_range("2026-01-05", periods=66)
        rising = pd.DataFrame(
            {
                "date": dates,
                "code": "A",
                "adjusted_close": [100 + offset for offset in range(66)],
            }
        )
        falling = pd.DataFrame(
            {
                "date": dates,
                "code": "B",
                "adjusted_close": [100 - 0.5 * offset for offset in range(66)],
            }
        )

        result = prepare(
            pd.concat([falling.iloc[::-1], rising.iloc[::-1]], ignore_index=True),
            periods=(5, 20, 60),
            future_periods=5,
        )
        stock_a = result.loc[result["code"] == "A"].reset_index(drop=True)

        self.assertTrue(stock_a["momentum_60d"].iloc[:60].isna().all())
        self.assertAlmostEqual(stock_a.loc[60, "momentum_60d"], 0.60)
        self.assertAlmostEqual(stock_a.loc[0, "future_return_5d"], 0.05)
        self.assertTrue(stock_a["future_return_5d"].iloc[-5:].isna().all())

    def test_uses_the_same_valid_stocks_for_every_window_on_each_date(self):
        _, calculate_ic, _ = load_functions()
        self.assertIsNotNone(calculate_ic, "共同样本 Rank IC 函数尚未实现")
        data = pd.DataFrame(
            {
                "date": ["2026-06-30"] * 4,
                "code": ["A", "B", "C", "D"],
                "momentum_5d": [0.04, 0.03, float("nan"), 0.01],
                "momentum_20d": [0.08, 0.06, 0.04, 0.02],
                "momentum_60d": [0.12, 0.09, 0.06, float("nan")],
                "future_return_5d": [0.03, 0.02, 0.01, 0.00],
            }
        )

        result = calculate_ic(data, periods=(5, 20, 60))

        self.assertEqual(result["valid_pair_count"].tolist(), [2, 2, 2])
        self.assertEqual(result["period"].tolist(), [5, 20, 60])

    def test_summarizes_rank_ic_separately_by_calendar_year(self):
        _, _, summarize = load_functions()
        self.assertIsNotNone(summarize, "年度稳定性汇总函数尚未实现")
        daily_ic = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2025-06-30", "2025-07-01", "2026-06-30", "2026-07-01"]
                ),
                "period": [20, 20, 20, 20],
                "valid_pair_count": [10, 10, 10, 10],
                "rank_ic": [0.10, -0.02, 0.06, 0.02],
            }
        )

        result = summarize(daily_ic).set_index("year")

        self.assertAlmostEqual(result.loc[2025, "mean_rank_ic"], 0.04)
        self.assertAlmostEqual(result.loc[2025, "positive_ic_ratio"], 0.50)
        self.assertAlmostEqual(result.loc[2026, "mean_rank_ic"], 0.04)
        self.assertAlmostEqual(result.loc[2026, "positive_ic_ratio"], 1.00)
        self.assertEqual(result.loc[2025, "valid_date_count"], 2)
        self.assertEqual(result.loc[2026, "valid_date_count"], 2)


if __name__ == "__main__":
    unittest.main()
