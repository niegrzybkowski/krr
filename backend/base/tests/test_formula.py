import unittest

from backend.base import Formula, State, Obs


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

    def test_given_singular_when_all_possibilities_then_gives_one(self):
        # given
        formula = Formula([
            "a"
        ]
        )
        # when
        possibilities = formula.get_all_posibilites()
        # then
        self.assertEqual(len(possibilities), 1)

    def test_given_singular_when_all_possibilities_then_gives_correct(self):
        # given
        formula = Formula([
            "a"
        ]
        )
        # when
        possibilities = formula.get_all_possibilities()
        # then
        self.assertCountEqual(
            [
                Obs(states=[State(name='a', holds=True)])
                ], 
            possibilities)

    def test_given_simple_when_all_possibilities_then_gives_three(self):
        # given
        formula = Formula([
            [
                "a",
                "or",
                "b"
            ]
        ]
        )
        # when
        possibilities = formula.get_all_possibilities()
        # then
        self.assertEqual(len(possibilities), 3)

    def test_given_simple_when_all_possibilities_then_gives_correct(self):
        # given
        formula = Formula([
            [
                "a",
                "or",
                "b"
            ]
        ]
        )
        # when
        possibilities = formula.get_all_possibilities()
        # then
        self.assertCountEqual(
            [
                Obs(states=[State(name='a', holds=True), State(name='b', holds=True)]),
                Obs(states=[State(name='a', holds=True), State(name='b', holds=False)]),
                Obs(states=[State(name='a', holds=False), State(name='b', holds=True)]),
                ], 
            possibilities)

    def test_given_nested_when_all_possibilities_then_gives_two(self):
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
            ]
        ]
        )
        # when
        possibilities = formula.get_all_possibilities()
        # then
        self.assertEqual(len(possibilities), 2)

    def test_given_nested_when_all_possibilities_then_gives_correct(self):
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
            ]
        ]
        )
        # when
        possibilities = formula.get_all_possibilities()
        # then
        self.assertCountEqual(
            [
                [State(name='a', holds=True), State(name='b', holds=True), State(name='c', holds=True)],
                [State(name='a', holds=True), State(name='b', holds=False), State(name='c', holds=False)],
                ],
            list(map(lambda x: x.states, possibilities)))


if __name__ == '__main__':
    unittest.main()
