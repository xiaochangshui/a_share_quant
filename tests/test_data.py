import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from a_share_quant.data import load_daily_data, validate_daily_data


class DailyDataTest(unittest.TestCase):
    def test_loads_types_preserves_code_and_sorts(self):
        raw = pd.DataFrame({
            "date": ["2026-01-03", "2026-01-02"],
            "code": ["000001", "000001"],
            "open": [10.2, 10.0], "close": [10.3, 10.1],
            "can_trade": [True, False],
        })
        with TemporaryDirectory() as directory:
            path = Path(directory) / "daily.csv"
            raw.to_csv(path, index=False)
            result = load_daily_data(path)
        self.assertEqual(result["code"].tolist(), ["000001", "000001"])
        self.assertEqual(result["date"].dt.strftime("%Y-%m-%d").tolist(), ["2026-01-02", "2026-01-03"])
        self.assertEqual(str(result["can_trade"].dtype), "bool")

    def test_rejects_invalid_rows_without_mutating_input(self):
        cases = [
            (pd.DataFrame({"date": ["2026-01-02"]}), "缺少必要字段"),
            (pd.DataFrame(columns=["date", "code", "open", "close", "can_trade"]), "为空"),
            (pd.DataFrame({"date": ["bad"], "code": ["A"], "open": [10], "close": [10], "can_trade": [True]}), "date"),
            (pd.DataFrame({"date": ["2026-01-02"], "code": ["A"], "open": [0], "close": [10], "can_trade": [True]}), "open"),
            (pd.DataFrame({"date": ["2026-01-02"], "code": ["A"], "open": [10], "close": [10], "can_trade": ["maybe"]}), "can_trade"),
        ]
        for data, message in cases:
            original = data.copy(deep=True)
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    validate_daily_data(data)
                pd.testing.assert_frame_equal(data, original)

    def test_rejects_duplicate_date_and_code(self):
        data = pd.DataFrame({
            "date": ["2026-01-02", "2026-01-02"], "code": ["A", "A"],
            "open": [10, 10], "close": [10, 10], "can_trade": [True, True],
        })
        with self.assertRaisesRegex(ValueError, "重复"):
            validate_daily_data(data)


if __name__ == "__main__":
    unittest.main()
