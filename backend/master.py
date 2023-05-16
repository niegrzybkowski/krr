from typing import List

from base import *
from pprint import pprint as pp

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


def main():
    """
    TODO:
        - ActionQuery       PM      M
        - FluentQuery       AK      M
        - UI Parsing        AK      M
        - Logical parsing   PM      M
        - Validation        --      W
    """
    termination = 10
    query = AgentQuery(agent=Agent(agents[2]), scenario=scenario, termination=termination)
    print(query.run())
    
    res = {}
    for state in states:
        # print(f'{"-"*50}\n{state:^50}\n{"-"*50}\n')
        res[state] = {"always holds": [], "sometimes holds": [], "never holds": []}
        for timepoint in range(termination+2):
            fluent_query = FluentQuery(
                scenario=scenario, termination=termination,
                fluent=State(state),
                timepoint=timepoint,
                mode='possibly')
            # print(fluent_query.run())
            _sometimes = fluent_query.run().find('sometimes') > 0
            fluent_query = FluentQuery(
                scenario=scenario, termination=termination,
                fluent=State(state),
                timepoint=timepoint,
                mode='necessary')
            _always = fluent_query.run().find(f'{state} always') > 0
            # print(fluent_query.run())
            # print(' -'*25)
            
            if _always:
                res[state]["always holds"].append(timepoint)
            elif _sometimes:
                res[state]["sometimes holds"].append(timepoint)
            else:
                res[state]["never holds"].append(timepoint)
    pp(res) # letter read not working because of preconditions


if __name__ == "__main__":
    main()
