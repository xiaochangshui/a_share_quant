import importlib
import unittest

import numpy as np
import pandas as pd


def load_function():
    try:
        module = importlib.import_module(
            "lessons.stage5_market_cap_neutralization"
        )
    except ModuleNotFoundError:
        return None
    return module.neutralize_by_market_cap


class MarketCapNeutralizationTest(unittest.TestCase):
    def test_returns_zero_residual_for_exact_linear_relation(self):
        neutralize = load_function()
        self.assertIsNotNone(neutralize, "市值中性化教学脚本尚未实现")
        data = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 3,
                "code": ["A", "B", "C"],
                "market_cap": np.exp([1.0, 2.0, 3.0]),
                "factor": [3.0, 5.0, 7.0],
            }
        )

        result = neutralize(data, factor_column="factor")

        np.testing.assert_allclose(result["log_market_cap"], [1.0, 2.0, 3.0])
        np.testing.assert_allclose(
            result["factor_size_predicted"],
            [3.0, 5.0, 7.0],
        )
        np.testing.assert_allclose(
            result["factor_size_neutral"],
            [0.0, 0.0, 0.0],
            atol=1e-12,
        )

    def test_fits_each_date_independently(self):
        neutralize = load_function()
        self.assertIsNotNone(neutralize, "市值中性化教学脚本尚未实现")
        market_caps = np.exp([1.0, 2.0, 3.0]).tolist() * 2
        data = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 3 + ["2026-01-06"] * 3,
                "code": ["A", "B", "C"] * 2,
                "market_cap": market_caps,
                "factor": [3.0, 5.0, 7.0, 9.0, 8.0, 7.0],
            }
        )

        result = neutralize(data, factor_column="factor")

        np.testing.assert_allclose(
            result["factor_size_neutral"],
            [0.0] * 6,
            atol=1e-12,
        )

    def test_keeps_unusable_cross_sections_as_nan(self):
        neutralize = load_function()
        self.assertIsNotNone(neutralize, "市值中性化教学脚本尚未实现")
        data = pd.DataFrame(
            {
                "date": ["2026-01-05"] * 4 + ["2026-01-06"] * 3,
                "code": ["A", "B", "C", "D", "A", "B", "C"],
                "market_cap": [100.0, 0.0, -1.0, float("nan"), 100.0, 100.0, 100.0],
                "factor": [1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 3.0],
            }
        )

        result = neutralize(data, factor_column="factor")

        self.assertTrue(result["factor_size_neutral"].isna().all())
        self.assertTrue(result.loc[1:3, "log_market_cap"].isna().all())


if __name__ == "__main__":
    unittest.main()
