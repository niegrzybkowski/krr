import unittest
from typing import List

from backend.base.action import Action
from backend.base.agent import Agent
from backend.base.exception import LogicException
from backend.base.formula import Formula
from backend.base.state import State
from backend.base.statement import EffectStatement, ReleaseStatement, Statement
from backend.base.timepoint import Obs


class ActionTest(unittest.TestCase):

    def setUp(self):
        self.statements: List[Statement] = [
            ReleaseStatement(action=Action('deliver letter'), agent=Agent('Postman'),
                             precondition=Formula(['letter sent']), postcondition=State('letter delivered'))
        ]
        self.obs: Obs = Obs(states=[
            State(name='letter ready', holds=True),
            State(name='letter sent', holds=True),
            State(name='letter delivered', holds=False),
            State(name='letter read', holds=False),
        ])

    def test_given_release_statement_in_the_same_action_when_run_then_multiple_results(self):
        # given
        action = Action('deliver letter')
        # when
        results = action.run(self.obs, self.statements)
        # then
        self.assertEqual(len(results), 2)

    def test_given_effect_statement_in_the_same_action_when_run_then_letter_not_ready_in_both(self):
        # given
        self.statements.append(
            EffectStatement(action=Action('deliver letter'), agent=Agent('Postman'),
                            precondition=Formula(['letter sent']), formula=Formula(['not', 'letter ready']))
        )
        action = Action('deliver letter')
        # when
        results = action.run(self.obs, self.statements)
        # then
        self.assertEqual(len(results), 2)

    def test_two_postcondition_regarding_same_state_raises_exception(self):
        # given
        self.statements.append(
            ReleaseStatement(action=Action('deliver letter'), agent=Agent('Postman'),
                             precondition=Formula(['letter sent']), postcondition=State('letter delivered'))
        )
        action = Action('deliver letter')
        # when
        with self.assertRaises(LogicException):
            # then
            action.run(self.obs, self.statements)

    def test_given_two_release_statements_in_the_same_action_when_run_then_multiple_results(self):
        # given
        self.statements.append(
            ReleaseStatement(action=Action('deliver letter'), agent=Agent('Postman'),
                             precondition=Formula(['letter sent']), postcondition=State('letter read'))
        )
        action = Action('deliver letter')
        # when
        results = action.run(self.obs, self.statements)
        # then
        self.assertEqual(len(results), 4)

    def test_given_release_statement_in_the_same_action_when_run_then_multiple_results_correct(self):
        # given
        action = Action('deliver letter')
        # when
        results = action.run(self.obs, self.statements)
        # then
        self.assertCountEqual(
            [
                Obs(states=[
                    State(name='letter ready', holds=True),
                    State(name='letter sent', holds=True),
                    State(name='letter delivered', holds=False),
                    State(name='letter read', holds=False),
                ]),
                Obs(states=[
                    State(name='letter ready', holds=True),
                    State(name='letter sent', holds=True),
                    State(name='letter delivered', holds=True),
                    State(name='letter read', holds=False),
                ]),
            ],
            results)

    def test_given_effect_and_release_statement_in_the_same_action_when_run_then_multiple_results_correct(self):
        # given
        self.statements.append(
            EffectStatement(action=Action('deliver letter'), agent=Agent('Postman'),
                            precondition=Formula(['letter sent']), formula=Formula(['not', 'letter ready']))
        )
        action = Action('deliver letter')
        # when
        results = action.run(self.obs, self.statements)
        # then
        self.assertCountEqual(
            [
                Obs(states=[
                    State(name='letter ready', holds=False),
                    State(name='letter sent', holds=True),
                    State(name='letter delivered', holds=False),
                    State(name='letter read', holds=False),
                ]),
                Obs(states=[
                    State(name='letter ready', holds=False),
                    State(name='letter sent', holds=True),
                    State(name='letter delivered', holds=True),
                    State(name='letter read', holds=False),
                ]),
            ],
            results)

    def test_given_two_release_statements_in_the_same_action_when_run_then_multiple_results_correct(self):
        # given
        self.statements.append(
            ReleaseStatement(action=Action('deliver letter'), agent=Agent('Postman'),
                             precondition=Formula(['letter sent']), postcondition=State('letter read'))
        )
        action = Action('deliver letter')
        # when
        results = action.run(self.obs, self.statements)
        # then
        self.assertCountEqual(
            [
                Obs(states=[
                    State(name='letter ready', holds=True),
                    State(name='letter sent', holds=True),
                    State(name='letter delivered', holds=False),
                    State(name='letter read', holds=False),
                ]),
                Obs(states=[
                    State(name='letter ready', holds=True),
                    State(name='letter sent', holds=True),
                    State(name='letter delivered', holds=True),
                    State(name='letter read', holds=False),
                ]),
                Obs(states=[
                    State(name='letter ready', holds=True),
                    State(name='letter sent', holds=True),
                    State(name='letter delivered', holds=False),
                    State(name='letter read', holds=True),
                ]),
                Obs(states=[
                    State(name='letter ready', holds=True),
                    State(name='letter sent', holds=True),
                    State(name='letter delivered', holds=True),
                    State(name='letter read', holds=True),
                ]),
            ],
            results)

    def test_given_two_opposite_cause_statements_in_the_same_action_when_run_then_correct(self):
        # given
        statements = [
            EffectStatement(action=Action('ACTION'), agent=Agent('Bill'),
                            precondition=Formula(), formula=Formula(['A'])),
            EffectStatement(action=Action('ACTION'), agent=Agent('Bill'),
                            precondition=Formula(), formula=Formula(['not', 'A'])),
        ]
        obs: Obs = Obs(states=[State(name='A', holds=False),
                               State(name='B', holds=False)])

        action = Action('ACTION')
        # when

        results = action.run(obs, statements)
        # then
        self.assertEqual(0, len(results))

    def test_given_two_slightly_opposite_cause_statements_in_the_same_action_when_run_then_correct(self):
        # given
        statements = [
            EffectStatement(action=Action('ACTION'), agent=Agent('Bill'),
                            precondition=Formula(), formula=Formula(['A', 'or', 'B'])),
            EffectStatement(action=Action('ACTION'), agent=Agent('Bill'),
                            precondition=Formula(), formula=Formula(['A', 'and', 'B'])),
        ]
        obs: Obs = Obs(states=[State(name='A', holds=False),
                               State(name='B', holds=False)])

        action = Action('ACTION')
        # when

        results = action.run(obs, statements)
        # then
        self.assertEqual(1, len(results))
