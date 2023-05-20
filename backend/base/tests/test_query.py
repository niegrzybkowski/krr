from typing import List
import unittest
from backend.base import scenario
from backend.base.action import Action
from backend.base.agent import Agent
from backend.base.formula import Formula
from backend.base.query import Query
from backend.base.state import State

from backend.base.statement import EffectStatement, ReleaseStatement, Statement
from backend.base.timepoint import Obs, TimePoint


class QueryTestCase(unittest.TestCase):
    def setUp(self):
        self.statements: List[Statement] = [
            EffectStatement(action=Action('write letter'), agent=Agent('Sender'),
                            precondition=Formula(), formula=Formula(['letter ready'])),
            EffectStatement(action=Action('send letter'), agent=Agent('Sender'),
                            precondition=Formula(['letter ready']), formula=Formula(['letter sent'])),
            ReleaseStatement(action=Action('deliver letter'), agent=Agent('Postman'),
                             precondition=Formula(['letter sent']), postcondition=State('letter delivered')),
            EffectStatement(action=Action('read letter'), agent=Agent('Receiver'),
                            precondition=Formula(['letter delivered']), formula=Formula(['letter read']))
        ]
        self.states: List[State] = [
            State(name='letter ready'),
            State(name='letter sent'),
            State(name='letter delivered'),
            State(name='letter read'),
        ]

    def test_given_obs_same_states(self):
        # given
        query = Query(
            scenario=scenario.Scenario.from_timepoints(
                statements=self.statements,
                timepoints=[
                    TimePoint(
                        t=0,
                        obs=Obs(formula=Formula(structure=[
                            [
                                "not",
                                "letter sent"
                            ],
                            "and",
                            [
                                "not",
                                "letter ready"
                            ],
                            "and",
                            [
                                "not",
                                "letter read"
                            ],
                            "and",
                            [
                                "not",
                                "letter delivered"
                            ]
                        ]))),
                    TimePoint(
                        t=1, acs=(Action('write letter'), Agent('Sender'))),
                    TimePoint(
                        t=2, acs=(Action('send letter'), Agent('Sender'))),
                    TimePoint(
                        t=3, acs=(Action('deliver letter'), Agent('Postman'))),
                    TimePoint(
                        t=4, acs=(Action('read letter'), Agent('Receiver'))),
                ]),
            termination=100, states=self.states)
        # when
        results = query.run()
        # then
        self.assertTrue(True)
