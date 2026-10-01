import unittest
import pandas as pd
from a_share_quant.factor import calculate_momentum


class FactorTest(unittest.TestCase):
    def test_calculates_within_stock_and_keeps_incomplete_windows_nan(self):
        dates = pd.bdate_range("2026-01-01", periods=22)
        data = pd.concat([
            pd.DataFrame({"date": dates, "code": "B", "close": range(200, 222)}),
            pd.DataFrame({"date": dates[::-1], "code": "A", "close": list(range(100, 122))[::-1]}),
        ], ignore_index=True)
        result = calculate_momentum(data, window=20)
        a = result[result["code"] == "A"].reset_index(drop=True)
        self.assertTrue(a.loc[:19, "factor_value"].isna().all())
        self.assertAlmostEqual(a.loc[20, "factor_value"], 0.20)

    def test_does_not_fill_missing_close(self):
        data = pd.DataFrame({"date": pd.bdate_range("2026-01-01", periods=4), "code": "A", "close": [10, None, 12, 13]})
        result = calculate_momentum(data, window=1)
        self.assertTrue(pd.isna(result.loc[1, "factor_value"]))
        self.assertTrue(pd.isna(result.loc[2, "factor_value"]))

    def test_rejects_invalid_window(self):
        with self.assertRaisesRegex(ValueError, "window"):
            calculate_momentum(pd.DataFrame(), window=0)


if __name__ == "__main__":
    unittest.main()
