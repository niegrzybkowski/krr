import unittest
from backend.base.action import Action
from backend.base.agent import Agent
from backend.base.formula import Formula
from backend.base.scenario import Scenario
from backend.base.state import State
from backend.base.timepoint import Obs, TimePoint


class ScenarioTestCase(unittest.TestCase):

    def test_given_obs_same_states(self):
        # given
        formula = Formula([
            "a"
        ])
        scenario = Scenario(
            statements=[],
            timepoints={
                2: TimePoint(t=2, obs=Obs(formula=formula))
            }
        )
        states = [State('a')]
        # when
        first_obs = scenario.get_first_obs(states=states)
        # then
        self.assertCountEqual(
            [Obs(states=[State(name='a', holds=True)])],
            first_obs
        )

    def test_given_obs_more_states(self):
        # given
        formula = Formula([
            "a"
        ])
        scenario = Scenario(
            statements=[],
            timepoints={
                2: TimePoint(t=2, obs=Obs(formula=formula))
            }
        )
        states = [State('a'), State('b')]
        # when
        first_obs = scenario.get_first_obs(states=states)
        # then
        self.assertCountEqual(
            [
                Obs(states=[State(name='a', holds=True), State(name='b', holds=True)]),
                Obs(states=[State(name='a', holds=True), State(name='b', holds=False)]),
            ],
            first_obs
        )

    def test_given_no_obs(self):
        # given
        formula = Formula([
            "a"
        ])
        scenario = Scenario(
            statements=[],
            timepoints={
                2: TimePoint(t=2, obs=None)
            }
        )
        states = [State('a'), State('b')]
        # when
        first_obs = scenario.get_first_obs(states=states)
        # then
        self.assertCountEqual(
            [
                Obs(states=[State(name='a', holds=True), State(name='b', holds=True)]),
                Obs(states=[State(name='a', holds=True), State(name='b', holds=False)]),
                Obs(states=[State(name='a', holds=False), State(name='b', holds=True)]),
                Obs(states=[State(name='a', holds=False), State(name='b', holds=False)]),
            ],
            first_obs
        )

    def test_given_acs_before_obs(self):
        # given
        formula = Formula([
            "a"
        ])
        scenario = Scenario(
            statements=[],
            timepoints={
                1: TimePoint(t=1, acs=(Action('action 1'), Agent('agent 1'))),
                2: TimePoint(t=2, obs=Obs(formula=formula))
            }
        )
        states = [State('a'), State('b')]
        # when
        first_obs = scenario.get_first_obs(states=states)
        # then
        self.assertCountEqual(
            [
                Obs(states=[State(name='a', holds=True), State(name='b', holds=True)]),
                Obs(states=[State(name='a', holds=True), State(name='b', holds=False)]),
                Obs(states=[State(name='a', holds=False), State(name='b', holds=True)]),
                Obs(states=[State(name='a', holds=False), State(name='b', holds=False)]),
            ],
            first_obs
        )
