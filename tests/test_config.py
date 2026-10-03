import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a_share_quant.config import load_research_config


class ResearchConfigTest(unittest.TestCase):
    def test_resolves_paths_relative_to_config_file(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_dir = root / "config"
            config_dir.mkdir()
            path = config_dir / "research.json"
            path.write_text(json.dumps({
                "data_path": "../data/daily.csv",
                "output_dir": "../result/run",
                "momentum_window": 20,
                "top_n": 2,
                "initial_cash": 100000,
                "costs": {
                    "commission_rate": 0.0003,
                    "minimum_commission": 5.0,
                    "stamp_tax_rate": 0.0005,
                    "slippage_rate": 0.001,
                },
            }), encoding="utf-8")
            config = load_research_config(path)
        self.assertEqual(config.data_path, (config_dir / "../data/daily.csv").resolve())
        self.assertEqual(config.output_dir, (config_dir / "../result/run").resolve())
        self.assertEqual(config.momentum_window, 20)
        self.assertAlmostEqual(config.costs.slippage_rate, 0.001)

    def test_rejects_missing_unknown_and_invalid_values(self):
        valid = {
            "data_path": "daily.csv", "output_dir": "result",
            "momentum_window": 20, "top_n": 2, "initial_cash": 100000,
            "costs": {"commission_rate": 0, "minimum_commission": 0, "stamp_tax_rate": 0, "slippage_rate": 0},
        }
        cases = [
            ({key: value for key, value in valid.items() if key != "top_n"}, "缺少配置字段"),
            ({**valid, "typo": 1}, "未知配置字段"),
            ({**valid, "momentum_window": 0}, "momentum_window"),
            ({**valid, "initial_cash": -1}, "initial_cash"),
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "research.json"
            for payload, message in cases:
                with self.subTest(message=message):
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        load_research_config(path)


if __name__ == "__main__":
    unittest.main()
