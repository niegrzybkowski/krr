from __future__ import annotations

from copy import deepcopy as copy
from dataclasses import dataclass
from typing import List

from . import agent as ag, timepoint as tp, statement as st
from . import ParsingException


@dataclass(slots=True)
class Action:
    name: str
    performed: bool = False

    @classmethod
    def from_ui(cls, data: dict) -> List[Action]:
        try:
            out = [cls(name=_name) for _name in data['ACTION']]
        except KeyError:
            raise ParsingException('Failed to parse action.')
        return out

    def run(
            self, agent: ag.Agent, obs: tp.Obs, statements: List[st.Statement]
    ) -> List[tp.Obs]:
        """run action by agent if """
        postconditions = [[]]
        for _statement in filter(lambda x: isinstance(x, st.EffectStatement), statements):
            if _statement.precondition.bool(obs=obs):
                agent.active = True
                self.performed = True
                postconditions[0].extend(copy(_statement.postcondition))

        for _statement in filter(lambda x: isinstance(x, st.ReleaseStatement), statements):
            if _statement.precondition.bool(obs=obs):
                agent.active = True
                self.performed = True

                psc = []
                psc2 = []
                for postcondition in postconditions:
                    temp = copy(postcondition)
                    temp.extend(copy(_statement.postcondition))
                    psc2.append(temp)
                    psc.append(copy(postcondition))

                postconditions.extend(psc)
                postconditions.extend(psc2)

        new_obs = []
        for postcondition in postconditions:
            # update states with all postconditions that can be applied
            temp = tp.Obs(states=copy(obs.states))
            temp |= tp.Obs(states=postcondition)
            new_obs.append(temp)

        return new_obs

    def __eq__(self, other: Action) -> bool:
        return self.name == other.name

    def __bool__(self) -> bool:
        return self.performed
