import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from a_share_quant.runner import run_research


class ResearchRunnerTest(unittest.TestCase):
    def test_writes_reproducible_research_artifacts(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            dates = pd.bdate_range("2026-01-01", periods=25)
            market = pd.concat([
                pd.DataFrame({"date": dates, "code": "000001", "open": range(100, 125), "close": range(100, 125), "can_trade": True}),
                pd.DataFrame({"date": dates, "code": "000002", "open": range(100, 75, -1), "close": range(100, 75, -1), "can_trade": True}),
            ], ignore_index=True)
            data_path = root / "daily.csv"
            market.to_csv(data_path, index=False)
            config_path = root / "research.json"
            config_path.write_text(json.dumps({
                "data_path": "daily.csv", "output_dir": "output",
                "momentum_window": 20, "top_n": 1, "initial_cash": 100000,
                "costs": {"commission_rate": 0, "minimum_commission": 0, "stamp_tax_rate": 0, "slippage_rate": 0},
            }), encoding="utf-8")

            first = run_research(config_path)
            first_equity = (root / "output/equity.csv").read_text(encoding="utf-8")
            second = run_research(config_path)
            second_equity = (root / "output/equity.csv").read_text(encoding="utf-8")

            expected = {"factors.csv", "targets.csv", "equity.csv", "positions.csv", "trades.csv", "report.json", "config_snapshot.json"}
            self.assertEqual({path.name for path in (root / "output").iterdir()}, expected)
            self.assertEqual(first_equity, second_equity)
            self.assertEqual(first.metrics, second.metrics)
            self.assertEqual(first.output_dir, root / "output")
            report = json.loads((root / "output/report.json").read_text(encoding="utf-8"))
            self.assertIn("cumulative_return", report["metrics"])
            self.assertEqual(report["row_counts"]["factors"], 50)
            snapshot = json.loads((root / "output/config_snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["data_path"], str(data_path.resolve()))


if __name__ == "__main__":
    unittest.main()
