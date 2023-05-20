from __future__ import annotations

from copy import deepcopy as copy
from dataclasses import dataclass
from typing import List, Tuple

from . import agent as ag, timepoint as tp, statement as st, state as state
from . import ParsingException


@dataclass(slots=True)
class Action:
    name: str

    @classmethod
    def from_ui(cls, data: dict) -> List[Action]:
        try:
            out = [cls(name=_name) for _name in data['ACTION']]
        except KeyError:
            raise ParsingException('Failed to parse action.')
        return out

    def run(
            self, obs: tp.Obs, statements: List[st.Statement]
    ) -> List[tp.Obs]:
        """run action by agent if """
        postconditions: List[List[state.State]] = []
        for _statement in filter(lambda x: isinstance(x, st.EffectStatement), statements):
            if _statement.precondition.bool(obs=obs):
                for post_obs in _statement.postconditions:
                    postconditions.append(post_obs.states)

        for _statement in filter(lambda x: isinstance(x, st.ReleaseStatement), statements):
            # _statement: state.State
            if _statement.precondition.bool(obs=obs):

                psc: List[List[state.State]] = []
                psc2 = []
                for postcondition in postconditions:
                    temp = copy(postcondition)
                    temp.extend(copy(_statement.postcondition))
                    psc.append(copy(postcondition))
                    psc2.append(temp)

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
