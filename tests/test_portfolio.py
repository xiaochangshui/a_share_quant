import unittest
import pandas as pd
from a_share_quant.portfolio import PortfolioState, apply_fills, build_orders


class PortfolioTest(unittest.TestCase):
    def test_applies_only_filled_trades_and_costs(self):
        state = PortfolioState.empty(10000)
        fills = pd.DataFrame([
            {"code": "A", "side": "buy", "quantity": 100, "fill_price": 10, "commission": 5, "stamp_tax": 0, "filled": True},
            {"code": "B", "side": "buy", "quantity": 100, "fill_price": 20, "commission": 5, "stamp_tax": 0, "filled": False},
        ])
        updated = apply_fills(state, fills)
        self.assertAlmostEqual(updated.cash, 8995)
        self.assertEqual(updated.positions.set_index("code").loc["A", "quantity"], 100)
        self.assertEqual(updated.positions.set_index("code").loc["A", "sellable_quantity"], 0)
        self.assertTrue(state.positions.empty)

    def test_builds_orders_from_target_minus_actual_value(self):
        state = PortfolioState(5000, pd.DataFrame({"code": ["A"], "quantity": [500.0], "sellable_quantity": [500.0]}))
        targets = pd.DataFrame({"code": ["A", "B"], "target_weight": [0.5, 0.5]})
        prices = pd.DataFrame({"code": ["A", "B"], "price": [20.0, 10.0]})
        orders = build_orders(state, targets, prices).set_index("code")
        self.assertAlmostEqual(orders.loc["A", "order_value"], -2500)
        self.assertAlmostEqual(orders.loc["B", "order_value"], 7500)
        self.assertEqual(orders.loc["A", "side"], "sell")


if __name__ == "__main__":
    unittest.main()
