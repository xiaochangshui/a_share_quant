import unittest
import pandas as pd
from a_share_quant.signal import generate_top_n_targets


class SignalTest(unittest.TestCase):
    def test_selects_each_date_and_breaks_ties_by_code(self):
        factors = pd.DataFrame({
            "date": ["2026-01-02"] * 4 + ["2026-01-05"] * 2,
            "code": ["B", "A", "C", "D", "A", "B"],
            "factor_value": [0.2, 0.2, 0.1, None, 0.3, 0.1],
        })
        result = generate_top_n_targets(factors, top_n=2)
        first = result[result["signal_date"] == pd.Timestamp("2026-01-02")]
        self.assertEqual(first["code"].tolist(), ["A", "B"])
        self.assertEqual(first["target_weight"].tolist(), [0.5, 0.5])
        self.assertEqual(result.groupby("signal_date")["target_weight"].sum().tolist(), [1.0, 1.0])

    def test_omits_date_without_valid_factor(self):
        factors = pd.DataFrame({"date": ["2026-01-02"], "code": ["A"], "factor_value": [None]})
        self.assertTrue(generate_top_n_targets(factors).empty)


if __name__ == "__main__":
    unittest.main()
