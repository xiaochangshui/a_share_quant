import importlib
import unittest

import pandas as pd


def load_functions():
    try:
        module = importlib.import_module("lessons.stage5_stock_pool_stability")
    except ModuleNotFoundError:
        return None, None
    return module.calculate_pool_daily_rank_ic, module.summarize_pool_rank_ic


class StockPoolStabilityTest(unittest.TestCase):
    def test_uses_historical_membership_for_each_date(self):
        calculate, _ = load_functions()
        self.assertIsNotNone(calculate, "股票池稳定性教学脚本尚未实现")
        research = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 3 + ["2026-01-06"] * 3,
                "code": ["A", "B", "C"] * 2,
                "factor": [1.0, 2.0, 3.0] * 2,
                "future_return": [1.0, 2.0, 0.0] * 2,
            }
        )
        membership = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 2 + ["2026-01-06"] * 2,
                "code": ["A", "B", "B", "C"],
                "pool": ["大盘股"] * 4,
            }
        )

        result = calculate(research, membership)

        self.assertEqual(result["member_count"].tolist(), [2, 2])
        self.assertAlmostEqual(result.loc[0, "rank_ic"], 1.0)
        self.assertAlmostEqual(result.loc[1, "rank_ic"], -1.0)

    def test_calculates_pools_separately_and_reports_missing_pairs(self):
        calculate, _ = load_functions()
        self.assertIsNotNone(calculate, "股票池稳定性教学脚本尚未实现")
        research = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 3,
                "code": ["A", "B", "C"],
                "factor": [1.0, 2.0, 3.0],
                "future_return": [1.0, float("nan"), 3.0],
            }
        )
        membership = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 5,
                "code": ["A", "B", "C", "A", "C"],
                "pool": ["全市场", "全市场", "全市场", "精选池", "精选池"],
            }
        )

        result = calculate(research, membership).set_index("pool")

        self.assertEqual(result.loc["全市场", "member_count"], 3)
        self.assertEqual(result.loc["全市场", "valid_pair_count"], 2)
        self.assertEqual(result.loc["全市场", "missing_pair_count"], 1)
        self.assertAlmostEqual(result.loc["精选池", "rank_ic"], 1.0)

    def test_summarizes_each_pool_with_sample_counts(self):
        _, summarize = load_functions()
        self.assertIsNotNone(summarize, "股票池稳定性汇总函数尚未实现")
        daily_ic = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2026-01-05", "2026-01-06", "2026-01-05", "2026-01-06"]
                ),
                "pool": ["全市场", "全市场", "大盘股", "大盘股"],
                "member_count": [4, 4, 2, 2],
                "valid_pair_count": [3, 2, 2, 1],
                "missing_pair_count": [1, 2, 0, 1],
                "rank_ic": [0.10, -0.02, 0.20, float("nan")],
            }
        )

        result = summarize(daily_ic).set_index("pool")

        self.assertAlmostEqual(result.loc["全市场", "mean_rank_ic"], 0.04)
        self.assertEqual(result.loc["全市场", "valid_date_count"], 2)
        self.assertAlmostEqual(result.loc["全市场", "positive_ic_ratio"], 0.5)
        self.assertAlmostEqual(
            result.loc["全市场", "average_valid_stock_count"],
            2.5,
        )
        self.assertEqual(result.loc["大盘股", "valid_date_count"], 1)
        self.assertAlmostEqual(result.loc["大盘股", "positive_ic_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
