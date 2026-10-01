import unittest
import pandas as pd
from a_share_quant.backtest import BacktestResult
from a_share_quant.metrics import calculate_metrics


class MetricsTest(unittest.TestCase):
    def test_calculates_cumulative_return_and_drawdown(self):
        equity = pd.DataFrame({"date": pd.bdate_range("2026-01-01", periods=4), "net_value": [1.0, 1.2, 0.9, 1.1]})
        result = calculate_metrics(BacktestResult(equity, pd.DataFrame(), pd.DataFrame()))
        self.assertAlmostEqual(result["cumulative_return"], 0.1)
        self.assertAlmostEqual(result["max_drawdown"], -0.25)

    def test_rejects_empty_or_non_positive_equity(self):
        with self.assertRaises(ValueError):
            calculate_metrics(BacktestResult(pd.DataFrame(), pd.DataFrame(), pd.DataFrame()))
        bad = pd.DataFrame({"date": ["2026-01-01"], "net_value": [0]})
        with self.assertRaises(ValueError):
            calculate_metrics(BacktestResult(bad, pd.DataFrame(), pd.DataFrame()))


if __name__ == "__main__":
    unittest.main()
