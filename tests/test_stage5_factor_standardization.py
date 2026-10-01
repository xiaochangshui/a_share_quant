import importlib
import unittest

import pandas as pd


def load_function():
    try:
        module = importlib.import_module("lessons.stage5_factor_standardization")
    except ModuleNotFoundError:
        return None
    return module.standardize_factors


class FactorStandardizationTest(unittest.TestCase):
    def test_converts_same_date_values_to_zscores(self):
        standardize = load_function()
        self.assertIsNotNone(standardize, "因子标准化教学脚本尚未实现")
        data = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 3,
                "code": ["A", "B", "C"],
                "momentum": [10.0, 20.0, 30.0],
            }
        )

        result = standardize(data, factor_columns=["momentum"])

        self.assertEqual(result["momentum_zscore"].tolist(), [-1.0, 0.0, 1.0])

    def test_standardizes_each_date_and_factor_independently(self):
        standardize = load_function()
        self.assertIsNotNone(standardize, "因子标准化教学脚本尚未实现")
        data = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 3 + ["2026-01-06"] * 3,
                "code": ["A", "B", "C"] * 2,
                "momentum": [10.0, 20.0, 30.0, 100.0, 200.0, 300.0],
                "quality": [30.0, 20.0, 10.0, 3.0, 2.0, 1.0],
            }
        )

        result = standardize(data, factor_columns=["momentum", "quality"])

        self.assertEqual(
            result["momentum_zscore"].tolist(),
            [-1.0, 0.0, 1.0, -1.0, 0.0, 1.0],
        )
        self.assertEqual(
            result["quality_zscore"].tolist(),
            [1.0, 0.0, -1.0, 1.0, 0.0, -1.0],
        )

    def test_keeps_missing_and_zero_standard_deviation_as_nan(self):
        standardize = load_function()
        self.assertIsNotNone(standardize, "因子标准化教学脚本尚未实现")
        data = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 3 + ["2026-01-06"] * 3,
                "code": ["A", "B", "C"] * 2,
                "momentum": [10.0, 20.0, float("nan"), 5.0, 5.0, 5.0],
            }
        )

        result = standardize(data, factor_columns=["momentum"])

        self.assertTrue(pd.isna(result.loc[2, "momentum_zscore"]))
        self.assertTrue(result.loc[3:5, "momentum_zscore"].isna().all())


if __name__ == "__main__":
    unittest.main()
