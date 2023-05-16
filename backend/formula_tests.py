import unittest
from base import Formula, State, Operator


class FormulaTestCase(unittest.TestCase):

    def test_given_fluent_when_bool_then_false(self):
        # given
        formula = Formula([
            State("a", holds=False)
        ])
        # when
        ans = bool(formula)
        # then
        self.assertFalse(ans)

    def test_given_not_fluent_when_bool_then_true(self):
        # given
        formula = Formula([
            "not", State("a", holds=False)
        ]
        )
        # when
        ans = bool(formula)
        # then
        self.assertTrue(ans)

    def test_given_fluent_and_fluent_when_bool_then_true(self):
        # given
        formula = Formula([
            State("a", holds=False),
            "and",
            State("b", holds=True)
        ])
        # when
        ans = bool(formula)
        # then
        self.assertFalse(ans)

    def test_given_fluent_implies_fluent_when_bool_then_true(self):
        # given
        formula = Formula([
            State("a", holds=False),
            "implies",
            State("b", holds=True)
        ])
        # when
        ans = bool(formula)
        # then
        self.assertTrue(ans)

    def test_given_nested_formula_when_bool_then_true(self):
        # given
        formula = Formula(
            [
                State("a", holds=True),
                "and",
                [
                    State("b", holds=False),
                    "or",
                    State("c", holds=True)
                ]
            ]
        )
        # when
        ans = bool(formula)
        # then
        self.assertTrue(ans, msg="Formula was true")

    def test_given_nested_formula_when_bool_then_false(self):
        # given
        formula = Formula(
            [
                State("a", holds=True),
                "and",
                [
                    State("b", holds=False),
                    "if and only if",
                    State("c", holds=True)
                ]
            ]
        )
        # when
        ans = bool(formula)
        # then
        self.assertFalse(ans, msg="Formula was false")

    def test_given_more_nested_formula_when_bool_then_false(self):
        # given
        formula = Formula([
            [
                State("a", holds=True),
                "and",
                [
                    State("b", holds=False),
                    "if and only if",
                    State("c", holds=True)
                ]
            ],
            "or",
            [
                State("a", holds=True),
                "and",
                [
                    State("b", holds=False),
                    "if and only if",
                    State("c", holds=True)
                ]
            ]
        ]
        )
        # when
        ans = bool(formula)
        # then
        self.assertFalse(ans, msg="Formula was false")


if __name__ == '__main__':
    unittest.main()
