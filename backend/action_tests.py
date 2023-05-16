import unittest
from typing import List

from base import *


class ActionTestCase(unittest.TestCase):  # TODO: changes function names

    def test_query_1_true(self):
        # given
        statements: List[Statement] = [
            EffectStatement(action=Action('write letter'), agent=Agent('Sender'),
                            precondition=Formula(), postcondition=[State('letter ready')]),
            EffectStatement(action=Action('send letter'), agent=Agent('Sender'),
                            precondition=Formula([State('letter ready')]), postcondition=[State('letter sent')]),
            ReleaseStatement(action=Action('deliver letter'), agent=Agent('Postman'),
                             precondition=Formula([State('letter sent')]), postcondition=[State('letter delivered')]),
            EffectStatement(action=Action('read letter'), agent=Agent('Receiver'),
                            precondition=Formula([State('letter delivered')]), postcondition=[State('letter read')])
        ]

        scenario: Scenario = Scenario.from_timepoints(
            statements=statements,
            timepoints=[
                TimePoint(t=0,
                          obs=Obs(states=[
                              State('letter sent', holds=False), State('letter ready', holds=False),
                              State('letter read', holds=False), State('letter delivered', holds=False)
                          ])),
                TimePoint(t=1, acs=(Action('write letter'), Agent('Sender'))),
                TimePoint(t=2, acs=(Action('send letter'), Agent('Sender'))),
                TimePoint(t=3, acs=(Action('deliver letter'), Agent('Postman'))),
                TimePoint(t=4, acs=(Action('read letter'), Agent('Receiver'))),
            ]
        )
        # when
        query = ActionQuery(action=Action('write letter'), scenario=scenario, termination=10)
        ans = query.run()
        # then
        self.assertEqual("Action write letter is performed in this Scenario", ans)

    def test_query_1_false_not_met_preconditions(self):
        # given
        statements: List[Statement] = [
            EffectStatement(action=Action('write letter'), agent=Agent('Sender'),
                            precondition=Formula([State('hold pen')]), postcondition=[State('letter ready')]),
            EffectStatement(action=Action('send letter'), agent=Agent('Sender'),
                            precondition=Formula([State('letter ready')]), postcondition=[State('letter sent')]),
            ReleaseStatement(action=Action('deliver letter'), agent=Agent('Postman'),
                             precondition=Formula([State('letter sent')]), postcondition=[State('letter delivered')]),
            EffectStatement(action=Action('read letter'), agent=Agent('Receiver'),
                            precondition=Formula([State('letter delivered')]), postcondition=[State('letter read')])
        ]

        scenario: Scenario = Scenario.from_timepoints(
            statements=statements,
            timepoints=[
                TimePoint(t=0,
                          obs=Obs(states=[
                              State('letter sent', holds=False), State('letter ready', holds=False),
                              State('letter read', holds=False), State('letter delivered', holds=False),
                              State('hold pen', holds=False)
                          ])),
                TimePoint(t=1, acs=(Action('write letter'), Agent('Sender'))),
                TimePoint(t=2, acs=(Action('send letter'), Agent('Sender'))),
                TimePoint(t=3, acs=(Action('deliver letter'), Agent('Postman'))),
                TimePoint(t=4, acs=(Action('read letter'), Agent('Receiver'))),
            ]
        )
        # when
        query = ActionQuery(action=Action('write letter'), scenario=scenario, termination=10)
        ans = query.run()
        # then
        self.assertEqual("Action write letter is performed in this Scenario", ans)

    def test_query_3(self):
        # given
        statements: List[Statement] = [
            EffectStatement(action=Action('write letter'), agent=Agent('Sender'),
                            precondition=Formula(), postcondition=[State('letter ready')]),
            EffectStatement(action=Action('send letter'), agent=Agent('Sender'),
                            precondition=Formula([State('letter ready')]), postcondition=[State('letter sent')]),
            ReleaseStatement(action=Action('deliver letter'), agent=Agent('Postman'),
                             precondition=Formula([State('letter sent')]), postcondition=[State('letter delivered')]),
            EffectStatement(action=Action('read letter'), agent=Agent('Receiver'),
                            precondition=Formula([State('letter delivered')]), postcondition=[State('letter read')])
        ]

        scenario: Scenario = Scenario.from_timepoints(
            statements=statements,
            timepoints=[
                TimePoint(t=0,
                          obs=Obs(states=[
                              State('letter sent', holds=False), State('letter ready', holds=False),
                              State('letter read', holds=False), State('letter delivered', holds=False)
                          ])),
                TimePoint(t=1, acs=(Action('write letter'), Agent('Sender'))),
                TimePoint(t=2, acs=(Action('send letter'), Agent('Sender'))),
                TimePoint(t=3, acs=(Action('deliver letter'), Agent('Postman'))),
                TimePoint(t=4, acs=(Action('read letter'), Agent('Receiver'))),
            ]
        )
        # when
        query = AgentQuery(agent=Agent('Receiver'), scenario=scenario, termination=10)
        ans = query.run()
        # then
        self.assertEqual("Agent Receiver is active in this Scenario", ans)


if __name__ == '__main__':
    unittest.main()
