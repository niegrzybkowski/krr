from typing import List
import unittest
from backend.base import scenario
from backend.base.action import Action
from backend.base.agent import Agent
from backend.base.formula import Formula
from backend.base.query import Query, ActionQuery, AgentQuery, FluentQuery
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
        self.scenario = scenario.Scenario.from_timepoints(
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
            ])

    def test_given_obs_same_states(self):
        # given
        query = Query(
            scenario=self.scenario,
            termination=100, states=self.states)
        # when
        results = query.run()
        # then
        self.assertEqual(len(results), 2)

    def test_when_action_query_given_run_then_action_performed(self):
        # given
        query = ActionQuery(
            scenario=self.scenario,
            termination=5, states=self.states, action=Action('write letter'), time=1)
        # when
        result = query.run()
        # then
        self.assertEqual(result, f"Action write letter is performed in moment 1 in this Scenario")

    def test_when_action_query_given_run_then_action_not_performed(self):
        # given
        query = ActionQuery(
            scenario=self.scenario,
            termination=5, states=self.states, action=Action('write letter'), time=3)
        # when
        result = query.run()
        # then
        self.assertEqual(result, f"Action write letter is not performed in moment 3 in this Scenario")

    def test_when_agent_query_given_run_then_action_performed(self):
        # given
        query = AgentQuery(
            scenario=self.scenario,
            termination=5, states=self.states, agent=Agent('Postman'))
        # when
        result = query.run()
        # then
        self.assertEqual(result, f"Agent Postman is active in this Scenario")

    def test_when_agent_query_given_run_then_agent_not_active(self):
        # given
        query = AgentQuery(
            scenario=self.scenario,
            termination=5, states=self.states, agent=Agent('Kaka'))
        # when
        result = query.run()
        # then
        self.assertEqual(result, f"Agent Kaka is not active in this Scenario")

    def test_when_fluent_query_given_run_then_necessary_at_t(self):
        # given
        query = FluentQuery(
            scenario=self.scenario,
            termination=5, states=self.states, fluent=State('letter sent'),
            mode='necessary', time=3
        )
        # when
        result = query.run()
        # then
        self.assertEqual(result, f"Fluent letter sent always holds at t=3")

    def test_when_fluent_query_given_run_then_possible_at_t(self):
        # given
        query = FluentQuery(
            scenario=self.scenario,
            termination=5, states=self.states, fluent=State('letter delivered'),
            mode='possibly', time=5
        )
        # when
        result = query.run()
        # then
        self.assertEqual(result, f"Fluent letter delivered sometimes holds at t=5")

    def test_when_fluent_query_given_run_then_not_hold_at_t(self):
        # given
        query = FluentQuery(
            scenario=self.scenario,
            termination=5, states=self.states, fluent=State('letter delivered'),
            mode='possibly', time=2
        )
        # when
        result = query.run()
        # then
        self.assertEqual(result, f"Fluent letter delivered never holds at t=2")
