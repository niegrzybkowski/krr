import unittest
import unittest
from base import Formula, State, Operator, Obs



class FormulaTestCase(unittest.TestCase):

    def test_given_fluent_when_bool_then_false(self):
        # given
        formula = Formula([
            "a"
        ])
        obs = Obs(states=[State("a", holds=False)])
        # when
        ans = formula.bool(obs)
        # then
        self.assertFalse(ans)

    def test_given_not_fluent_when_bool_then_true(self):
        # given
        formula = Formula([
            "not", "a"
        ]
        )
        obs = Obs(states=[State("a", holds=False)])
        # when
        ans = formula.bool(obs)
        # then
        self.assertTrue(ans)

    def test_given_fluent_and_fluent_when_bool_then_true(self):
        # given
        formula = Formula([
            "a",
            "and",
            "b",
        ])
        obs = Obs([
            State("a", holds=False),
            State("b", holds=True)
        ])
        # when
        ans = formula.bool(obs)
        # then
        self.assertFalse(ans)

    def test_given_fluent_implies_fluent_when_bool_then_true(self):
        # given
        formula = Formula([
            "a",
            "implies",
            "b",
        ])
        obs = Obs([
            State("a", holds=False),
            State("b", holds=True)
        ])
        # when
        ans = formula.bool(obs)
        # then
        self.assertTrue(ans)

    def test_given_nested_formula_when_bool_then_true(self):
        # given
        formula = Formula(
            [
                "a",
                "and",
                [
                    "b",
                    "or",
                    "c",
                ]
            ]
        )
        obs = Obs([
            State("a", holds=True),
            State("b", holds=False),
            State("c", holds=True)
        ])
        # when
        ans = formula.bool(obs)
        # then
        self.assertTrue(ans, msg="Formula was true")

    def test_given_nested_formula_when_bool_then_false(self):
        # given
        formula = Formula(
            [
                "a",
                "and",
                [
                    "b",
                    "if and only if",
                    "c"
                ]
            ]
        )
        obs = Obs([
            State("a", holds=True),
            State("b", holds=False),
            State("c", holds=True)
        ])
        # when
        ans = formula.bool(obs)
        # then
        self.assertFalse(ans, msg="Formula was false")

    def test_given_more_nested_formula_when_bool_then_false(self):
        # given
        formula = Formula([
            [
                "a",
                "and",
                [
                    "b",
                    "if and only if",
                    "c",
                ]
            ],
            "or",
            [
                "a",
                "and",
                [
                    "b",
                    "if and only if",
                    "c",
                ]
            ]
        ]
        )
        obs = Obs([
            State("a", holds=True),
            State("b", holds=False),
            State("c", holds=True)
        ])
        # when
        ans = formula.bool(obs)
        # then
        self.assertFalse(ans, msg="Formula was false")


if __name__ == '__main__':
    unittest.main()
