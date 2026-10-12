import importlib
import unittest
from unittest.mock import patch

import numpy as np


def load_functions():
    try:
        module = importlib.import_module("lessons.stage7_rqalpha_momentum")
    except ModuleNotFoundError:
        return None, None
    return module.calculate_momentum_scores, module.select_target_weights


class RQAlphaMomentumTest(unittest.TestCase):
    def test_init_does_not_overwrite_rqalpha_read_only_universe(self):
        module = importlib.import_module("lessons.stage7_rqalpha_momentum")

        class ContextWithReadOnlyUniverse:
            @property
            def universe(self):
                return set()

        context = ContextWithReadOnlyUniverse()
        with patch.object(module, "update_universe") as update:
            module.init(context)

        self.assertEqual(context.stock_pool, list(module.UNIVERSE))
        update.assert_called_once_with(context.stock_pool)

    def test_calculates_twenty_day_momentum_from_twenty_one_closes(self):
        calculate, _ = load_functions()
        self.assertIsNotNone(calculate, "RQAlpha 动量教学脚本尚未实现")
        histories = {
            "A": np.array([10.0] + [10.2] * 19 + [11.0]),
            "B": np.array([20.0] + [19.8] * 19 + [19.0]),
            "SHORT": np.array([10.0] * 20),
            "MISSING": np.array([10.0] * 20 + [np.nan]),
        }

        result = calculate(histories, window=20)

        self.assertAlmostEqual(result["A"], 0.10)
        self.assertAlmostEqual(result["B"], -0.05)
        self.assertNotIn("SHORT", result)
        self.assertNotIn("MISSING", result)

    def test_selects_top_scores_with_stable_tie_break_and_cash_buffer(self):
        _, select = load_functions()
        self.assertIsNotNone(select, "RQAlpha 目标权重函数尚未实现")

        result = select(
            {"B": 0.08, "C": 0.03, "A": 0.08},
            top_n=2,
            investable_weight=0.95,
        )

        self.assertEqual(list(result), ["A", "B"])
        self.assertAlmostEqual(result["A"], 0.475)
        self.assertAlmostEqual(result["B"], 0.475)
        self.assertAlmostEqual(sum(result.values()), 0.95)


if __name__ == "__main__":
    unittest.main()
