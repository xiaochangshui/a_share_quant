import importlib
import unittest

import numpy as np


class RQAlphaReversalTest(unittest.TestCase):
    def test_five_day_loss_gets_higher_reversal_score(self):
        module = importlib.import_module("lessons.stage7_rqalpha_reversal")
        histories = {
            "A": np.array([10, 10, 10, 10, 10, 9], dtype=float),
            "B": np.array([10, 10, 10, 10, 10, 11], dtype=float),
            "SHORT": np.array([10, 10, 10, 10, 9], dtype=float),
            "MISSING": np.array([10, 10, 10, 10, 10, np.nan]),
        }

        scores = module.calculate_reversal_scores(histories, window=5)

        self.assertAlmostEqual(scores["A"], 0.1)
        self.assertAlmostEqual(scores["B"], -0.1)
        self.assertNotIn("SHORT", scores)
        self.assertNotIn("MISSING", scores)

    def test_selects_two_highest_reversal_scores(self):
        module = importlib.import_module("lessons.stage7_rqalpha_reversal")

        weights = module.select_target_weights(
            {"B": -0.1, "C": 0.03, "A": 0.1},
            top_n=2,
            investable_weight=0.95,
        )

        self.assertEqual(weights, {"A": 0.475, "C": 0.475})


if __name__ == "__main__":
    unittest.main()
