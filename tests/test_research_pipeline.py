import unittest
import pandas as pd
from a_share_quant.backtest import CostConfig, run_backtest
from a_share_quant.data import validate_daily_data
from a_share_quant.factor import calculate_momentum
from a_share_quant.metrics import calculate_metrics
from a_share_quant.signal import generate_top_n_targets


class ResearchPipelineTest(unittest.TestCase):
    def test_runs_reproducible_pipeline_without_same_day_execution(self):
        dates = pd.bdate_range("2026-01-01", periods=25)
        market = pd.concat([
            pd.DataFrame({"date": dates, "code": "A", "open": range(100, 125), "close": range(100, 125), "can_trade": True}),
            pd.DataFrame({"date": dates, "code": "B", "open": range(100, 75, -1), "close": range(100, 75, -1), "can_trade": True}),
        ], ignore_index=True)
        validate_daily_data(market)
        targets = generate_top_n_targets(calculate_momentum(market), top_n=1)
        first = targets["signal_date"].min()
        one = run_backtest(market, targets, 100000, CostConfig(0, 0, 0, 0))
        two = run_backtest(market, targets, 100000, CostConfig(0, 0, 0, 0))
        self.assertTrue((one.trades["execution_date"] > one.trades["signal_date"]).all())
        self.assertEqual(first, dates[20])
        self.assertFalse(one.equity.empty)
        self.assertIn("cumulative_return", calculate_metrics(one))
        pd.testing.assert_frame_equal(one.equity, two.equity)


if __name__ == "__main__":
    unittest.main()
