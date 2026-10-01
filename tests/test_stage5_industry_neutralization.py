import importlib
import unittest

import pandas as pd


def load_function():
    try:
        module = importlib.import_module(
            "lessons.stage5_industry_neutralization"
        )
    except ModuleNotFoundError:
        return None
    return module.neutralize_by_industry_mean


class IndustryNeutralizationTest(unittest.TestCase):
    def test_subtracts_same_date_industry_mean(self):
        neutralize = load_function()
        self.assertIsNotNone(neutralize, "行业中性化教学脚本尚未实现")
        data = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 4,
                "code": ["A", "B", "C", "D"],
                "industry": ["科技", "科技", "银行", "银行"],
                "factor": [3.0, 1.0, 10.0, 8.0],
            }
        )

        result = neutralize(data, factor_column="factor")

        self.assertEqual(
            result["factor_industry_mean"].tolist(),
            [2.0, 2.0, 9.0, 9.0],
        )
        self.assertEqual(
            result["factor_industry_neutral"].tolist(),
            [1.0, -1.0, 1.0, -1.0],
        )

    def test_calculates_each_date_independently(self):
        neutralize = load_function()
        self.assertIsNotNone(neutralize, "行业中性化教学脚本尚未实现")
        data = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 2 + ["2026-01-06"] * 2,
                "code": ["A", "B"] * 2,
                "industry": ["科技"] * 4,
                "factor": [3.0, 1.0, 30.0, 10.0],
            }
        )

        result = neutralize(data, factor_column="factor")

        self.assertEqual(
            result["factor_industry_neutral"].tolist(),
            [1.0, -1.0, 10.0, -10.0],
        )

    def test_handles_missing_values_and_single_stock_industry(self):
        neutralize = load_function()
        self.assertIsNotNone(neutralize, "行业中性化教学脚本尚未实现")
        data = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 4,
                "code": ["A", "B", "C", "D"],
                "industry": ["单股票行业", "科技", "科技", None],
                "factor": [5.0, float("nan"), 3.0, 4.0],
            }
        )

        result = neutralize(data, factor_column="factor")

        self.assertEqual(result.loc[0, "factor_industry_neutral"], 0.0)
        self.assertTrue(pd.isna(result.loc[1, "factor_industry_neutral"]))
        self.assertEqual(result.loc[2, "factor_industry_neutral"], 0.0)
        self.assertTrue(pd.isna(result.loc[3, "factor_industry_neutral"]))


if __name__ == "__main__":
    unittest.main()
