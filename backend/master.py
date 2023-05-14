from typing import List, Tuple

from base import *
from itertools import product

TERMINATION = 10

agents: List[str] = ['Sender', 'Postman', 'Receiver']

actions: List[str] = [
    'write letter', 'send letter', 'deliver mail', 'read letter'
]

states: List[str] = [
    'letter ready',
    'letter sent',
    'letter delivered',
    'letter read',
]

statements: List[Statement] = [
    EffectStatement(action=Action('write letter'), agent=Agent('Sender'),
                    precondition=Formula(), postcondition=[State('letter ready')]),
    EffectStatement(action=Action('send letter'), agent=Agent('Sender'),
                    precondition=Formula([State('letter ready')]), postcondition=[State('letter sent')]),
    ReleaseStatement(action=Action('deliver mail'), agent=Agent('Postman'),
                     precondition=Formula([State('letter sent')]), postcondition=[State('letter delivered')]),
    EffectStatement(action=Action('read mail'), agent=Agent('Receiver'),
                    precondition=Formula([State('letter delivered')]), postcondition=[State('letter read')])
]

scenario: Scenario = Scenario.from_timepoints(
    statements=statements,
    timepoints=[
        TimePoint(t=0,
                  obs=[
                      State('letter sent', holds=False), State('letter ready', holds=False),
                      State('letter read', holds=False), State('letter delivered', holds=False)
                  ]),
        TimePoint(t=1, acs=(Action('write letter'), Agent('Sender'))),
        TimePoint(t=2, acs=(Action('send letter'), Agent('Sender'))),
        TimePoint(t=3, acs=(Action('deliver mail'), Agent('Postman'))),
        TimePoint(t=4, acs=(Action('read letter'), Agent('Receiver'))),
    ]
)


# # Query 1 can be performed?
#
# # input: obs, realization, TERMINATION
# t = 7
# query1 = (Action('letter sent'), t, scenario)
#
# # possible_realizations: List[List[Tuple[Action, Agent, int]]]
#
# if t >= TERMINATION:
#     ans = False
#     # return
# val = next(filter(lambda item: item[2] == t, acs), None)
# if not val:
#     ans = val[0] == Action('letter sent')
#     # return
#
# for time in range(1, t + 1):
#     pass
#
# t = 8
#
# obs: t = 8?


def main():
    termination = 10
    query = AgentQuery(agent=Agent(agents[1]), scenario=scenario, termination=termination)
    print(query.run())


if __name__ == "__main__":
    main()
